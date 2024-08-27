# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

# Third Party Libraries
import humps

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# CMS Common Library
from cms_common.boto3_wrappers.dynamo_crud import DynHelpers

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_sns.client import SNSClient
    from mypy_boto3_sns.type_defs import CreateTopicResponseTypeDef
else:
    SNSClient = object
    CreateTopicResponseTypeDef = Dict[str, Any]

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_sns_client() -> SNSClient:
    return boto3.client(
        "sns", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(
    event: Dict[str, Any], context: LambdaContext
) -> Union[Union[Dict[str, Any], bool], object]:
    operations = {
        "getUserSubscriptions": get_user_subscriptions,
        "updateUserSubscriptions": update_user_subscriptions,
    }
    try:
        arguments = humps.decamelize(event["arguments"])

        return operations[event["info"]["fieldName"]](arguments)
    except KeyError as err:
        logger.error(
            "KeyError occured",
            exc_info=True,
        )
        raise err
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error(
            msg=f"Error while performing {event['info']['fieldName']} operation",
            exc_info=True,
        )
        raise err


@tracer.capture_method
def update_user_subscriptions(arguments: Dict[str, Any]) -> bool:
    email = arguments["email"]
    alarms = arguments["alarms"]

    # get current user subscriptions with subscription arns
    user_subscriptions = get_user_subscriptions_with_subscription_arns(email)

    # create dictionaries for fast look up
    new_subscriptions = {
        f"{os.environ['SNS_TOPIC_PREFIX']}-{alarm['alarm_type']}-{alarm['vin']}": alarm
        for alarm in alarms
    }
    old_subscriptions = {
        alarm["topic_key"]: alarm for alarm in user_subscriptions["alarms"]
    }

    # empty updated items list
    update_batches: List[List[Dict[str, Any]]] = [[]]

    for topic_name in new_subscriptions:
        new_subscription = new_subscriptions[topic_name]
        old_subscription = old_subscriptions.get(topic_name, None)

        topic_arn = get_sns_client().create_topic(
            Name=f"{os.environ['SNS_TOPIC_PREFIX']}-{new_subscription['alarm_type']}-{new_subscription['vin']}",
            Tags=[{"Key": "AlertsUUID", "Value": os.environ["DEPLOYMENT_UUID"]}],
            Attributes={"KmsMasterKeyId": os.environ["SNS_TOPIC_GENERAL_KEY_ID"]},
        )["TopicArn"]

        item = update_subscriptions_and_return_updated_item(
            email, new_subscription, old_subscription, topic_arn
        )

        # add item to update_batches if item is not None
        if item:
            # if the last list in update_batche is not at max capacity then
            if len(update_batches[-1]) < DynHelpers.MAX_ITEM_PER_BATCH_IN_BATCH_WRITE:
                # append the new item to the last list
                update_batches[-1].append(item)
            else:
                # create a new list and add this item
                update_batches.append([item])

    # for each list in updated_items we batch write them to dynamodb
    for batch in update_batches:
        if len(batch) > 0:
            DynHelpers.dyn_batch_write(
                os.environ["USER_EMAIL_SUBSCRIPTIONS_TABLE"], batch
            )

    return True


@tracer.capture_method
def get_user_subscriptions(arguments: Dict[str, Any]) -> Dict[str, Any]:
    user_subscription_items = DynHelpers.dyn_query(
        table_name=os.environ["USER_EMAIL_SUBSCRIPTIONS_TABLE"],
        key_condition_expression="email=:email",
        projection_expression="#E, #V, #A",
        expression_attribute_names={
            "#E": "email",
            "#V": "vin",
            "#A": "alarm_type",
        },
        expression_attribute_values={":email": arguments["email"]},
    )

    alarms = list(
        map(
            lambda item: {
                "vin": item["vin"],
                "alarm_type": item["alarm_type"],
            },
            user_subscription_items,
        )
    )

    return humps.camelize({"email": arguments["email"], "alarms": alarms})


# -------------------- Additional Helper Functions -----------------------------
@tracer.capture_method
def get_user_subscriptions_with_subscription_arns(email: str) -> Dict[str, Any]:
    user_subscription_items = DynHelpers.dyn_query(
        table_name=os.environ["USER_EMAIL_SUBSCRIPTIONS_TABLE"],
        key_condition_expression="email=:email",
        expression_attribute_values={":email": email},
    )
    alarms = list(
        map(
            lambda item: {
                "vin": item["vin"],
                "alarm_type": item["alarm_type"],
                "subscription_arn": item.get("subscription_arn", ""),
                "topic_key": item["topic_key"],
            },
            user_subscription_items,
        ),
    )

    return {"email": email, "alarms": alarms}


@tracer.capture_method
def update_subscriptions_and_return_updated_item(
    email: str,
    new_subscription: Dict[str, Any],
    old_subscription: Optional[Dict[str, Any]],
    topic_arn: str,
) -> Optional[Dict[str, Any]]:
    topic_key = f"{os.environ['SNS_TOPIC_PREFIX']}-{new_subscription['alarm_type']}-{new_subscription['vin']}"
    # now we check if the new alarm is trying to enable or disable email notifcations
    item = None
    if (
        old_subscription is None and new_subscription["email_enabled"]
    ):  # old alarm does not exist and user wants to subscribe
        # to enable it we subscribe to it and add its subscription_arn to updated alarm
        subscription_arn = get_sns_client().subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
            ReturnSubscriptionArn=True,
        )["SubscriptionArn"]

        # this is the new item to be written to dynamodb
        item = {
            "operation": "PUT",
            "item": {
                "email": email,
                "subscription_arn": subscription_arn,
                "vin": new_subscription["vin"],
                "alarm_type": new_subscription["alarm_type"],
                "topic_key": topic_key,
            },
        }
    elif (
        old_subscription and not new_subscription["email_enabled"]
    ):  # old alarm exists and user wants to subscribe
        # to disable it we look at the old alarm object and using that subscription arn we unsubscribe
        get_sns_client().unsubscribe(
            SubscriptionArn=old_subscription["subscription_arn"]
        )

        # this is the new item to be written to dynamodb
        item = {
            "operation": "DELETE",
            "key": {
                "email": email,
                "topic_key": topic_key,
            },
        }

    return item
