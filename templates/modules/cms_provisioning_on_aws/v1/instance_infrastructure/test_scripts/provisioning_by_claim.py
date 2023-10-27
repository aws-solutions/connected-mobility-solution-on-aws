# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional
from urllib import request
from uuid import uuid4

# Third Party Libraries
import boto3
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig  # type: ignore
from awscrt import exceptions, mqtt
from awsiot import iotidentity, mqtt_connection_builder  # type: ignore
from botocore import session as boto_session
from mypy_boto3_iot.client import IoTClient

# Connected Mobility Solution on AWS
from .dynamodb_helpers import (
    add_vehicle_to_authorized_vehicles_table,
    get_authorized_vehicles_table_name,
)

# Provisioning_template_name
TEMPLATE_NAME = "cms-vehicle-provisioning-template"
# Root CA URL
CA_FILE_URL = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
# Name of the claim certificate/key pair in aws secret manager.
IOT_CLAIM_CERTS_NAME = "dev/cms-provisioning-on-aws-stack-dev/provisioning-credentials"
# Connection port. AWS IoT supports 443 and 8883
REMOTE_PORT = 443


@lru_cache(maxsize=128)
def get_iot_client() -> IoTClient:
    return boto3.client("iot")


@dataclass(frozen=True)
class ClaimCredentials:
    certificate_pem: bytes
    private_key: bytes
    ca_certificate: bytes


@dataclass(frozen=True)
class ProvisionedCredentials:
    certificate_pem: bytes
    private_key: bytes
    certificate_id: str


class ProvisioningByClaim:  # pylint: disable=too-many-instance-attributes
    # For the Provisioning by Claim, ClientID can be any random string.
    create_keys_and_certificate_response = None
    register_thing_response = None
    provisioned_credentials: Optional[ProvisionedCredentials] = None

    def __init__(self, vin: str) -> None:
        self.vin = vin
        self.template_parameters = '{"vin":"' + self.vin + '"}'

        # For the Provisioning by Claim, ClientID can be any random string.
        self.provisioning_client_id = str(uuid4())
        self.connect_client_id = f"Vehicle_{self.vin}"

        self.iot_endpoint = self.find_iot_endpoint()
        self.claim_credentials = self.fetch_claim_credentials()

        self.mqtt_connection = mqtt_connection_builder.mtls_from_bytes(
            endpoint=self.iot_endpoint,
            port=REMOTE_PORT,
            cert_bytes=self.claim_credentials.certificate_pem,
            pri_key_bytes=self.claim_credentials.private_key,
            ca_bytes=self.claim_credentials.ca_certificate,
            on_connection_interrupted=self.on_connection_interrupted,
            on_connection_resumed=self.on_connection_resumed,
            client_id=self.provisioning_client_id,
            clean_session=False,
            keep_alive_secs=30,
            http_proxy_options=None,
        )

    # Callback when connection is accidentally lost.
    def on_connection_interrupted(
        self, connection: mqtt.Connection, error: exceptions.AwsCrtError, **kwargs: Any
    ) -> None:
        print(f"Connection interrupted. error: {error}")

    # Callback when an interrupted connection is re-established.
    def on_connection_resumed(
        self,
        connection: mqtt.Connection,
        return_code: mqtt.ConnectReturnCode,
        session_present: bool,
        **kwargs: Any,
    ) -> None:
        print(
            f"Connection resumed. return_code: {return_code} session_present: {session_present}"
        )

        if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
            print("Session did not persist. Resubscribing to existing topics...")
            resubscribe_future, _ = connection.resubscribe_existing_topics()

            # Cannot synchronously wait for resubscribe result because we're on
            # the connection's event-loop thread, evaluate result with a
            # callback instead.
            resubscribe_future.add_done_callback(self.on_resubscribe_complete)

    def on_resubscribe_complete(self, resubscribe_future: Any) -> None:
        resubscribe_results = resubscribe_future.result()
        print(f"Resubscribe results: {resubscribe_results}")

        for topic, qos in resubscribe_results["topics"]:
            if qos is None:
                raise Exception(  # pylint: disable=W0719
                    f"Server rejected resubscribe to topic: {topic}"
                )  # pylint: disable=W0718

    def createkeysandcertificate_execution_rejected(
        self, rejected: iotidentity.ErrorResponse
    ) -> None:
        raise Exception(  # pylint: disable=W0719
            f"""
            CreateKeysAndCertificate Request rejected with
            code:'{rejected.error_code}' message:'{rejected.error_message}'
            statuscode:'{rejected.status_code}'
            """
        )

    def registerthing_execution_rejected(
        self, rejected: iotidentity.ErrorResponse
    ) -> None:
        raise Exception(  # pylint: disable=W0719
            f"""
            RegisterThing Request rejected with
            code:'{rejected.error_code}' message:'{rejected.error_message}'
            statuscode:'{rejected.status_code}'
            """
        )

    def on_publish_create_keys_and_certificate(self, future: Any) -> None:
        try:
            future.result()  # raises exception if publish failed
            print("Published CreateKeysAndCertificate request..")
        except Exception as exception:  # pylint: disable=W0718
            print(f"Failed to publish CreateKeysAndCertificate request: {exception}")
            raise

    def on_publish_register_thing(self, future: Any) -> None:
        try:
            future.result()  # raises exception if publish failed
            print("Published RegisterThing request..")
        except Exception as exception:  # pylint: disable=W0718
            print(f"Failed to publish RegisterThing request: {exception}")
            raise

    def wait_for_register_thing_response(self) -> None:
        # Wait for the response.
        loop_count = 0
        while loop_count < 20 and self.register_thing_response is None:
            if self.register_thing_response is not None:
                break
            loop_count += 1
            print(
                "Waiting... RegisterThingResponse: "
                + json.dumps(self.register_thing_response)
            )
            time.sleep(1)

    def registerthing_execution_accepted(
        self, response: iotidentity.RegisterThingResponse
    ) -> None:
        self.register_thing_response = response
        print(f"Received a new message {self.register_thing_response}")

    def wait_for_create_keys_and_certificate_response(self) -> None:
        # Wait for the response.
        loop_count = 0
        while loop_count < 10 and self.create_keys_and_certificate_response is None:
            if self.create_keys_and_certificate_response is not None:
                break
            print(
                "Waiting... CreateKeysAndCertificateResponse: "
                + json.dumps(self.create_keys_and_certificate_response)
            )
            loop_count += 1
            time.sleep(1)

    def createkeysandcertificate_execution_accepted(
        self, response: iotidentity.CreateKeysAndCertificateResponse
    ) -> None:
        self.create_keys_and_certificate_response = response
        print("createkeysandcertificate succeded.")

        self.provisioned_credentials = ProvisionedCredentials(
            certificate_id=self.create_keys_and_certificate_response.certificate_id,
            certificate_pem=bytes(
                self.create_keys_and_certificate_response.certificate_pem,
                encoding="utf-8",
            ),
            private_key=bytes(
                self.create_keys_and_certificate_response.private_key, encoding="utf-8"
            ),
        )

    def find_iot_endpoint(self) -> str:
        # Retrieve the Amazon Trust Services (ATS) endpoint for IoT Core.
        response = get_iot_client().describe_endpoint(endpointType="iot:Data-ATS")
        return response["endpointAddress"]

    def fetch_claim_credentials(self) -> ClaimCredentials:
        # Fetch claim certificate and private key.
        client = boto_session.get_session().create_client("secretsmanager")
        cache_config = SecretCacheConfig()
        cache = SecretCache(config=cache_config, client=client)
        secret_string = cache.get_secret_string(IOT_CLAIM_CERTS_NAME)
        secret_json = json.loads(secret_string)

        # Fetch CA Root certificate
        with request.urlopen(CA_FILE_URL) as url:
            ca_bytes = url.read()

        return ClaimCredentials(
            certificate_pem=bytes(secret_json["certificatePem"], encoding="utf-8"),
            private_key=bytes(secret_json["keyPair"]["PrivateKey"], encoding="utf-8"),
            ca_certificate=ca_bytes,
        )

    def send_vehicle_provisioning_request(self) -> bool:
        print(f"Connecting to {self.iot_endpoint} ...")
        connected_future = self.mqtt_connection.connect()
        identity_client = iotidentity.IotIdentityClient(self.mqtt_connection)

        # Wait for connection to be fully established.
        # Note that it's not necessary to wait, commands issued to the
        # mqtt_connection before its fully connected will simply be queued.
        # But this sample waits here so it's obvious when a connection
        # fails or succeeds.
        connected_future.result()
        print("Connected!")

        success = False
        try:
            # Subscribe to necessary topics.
            # Note that it **is** important to wait for "accepted/rejected" subscriptions
            # to succeed before publishing the corresponding "request".

            createkeysandcertificate_subscription_request = (
                iotidentity.CreateKeysAndCertificateSubscriptionRequest()
            )

            print("Subscribing to CreateKeysAndCertificate Accepted topic...")
            (
                createkeysandcertificate_subscribed_accepted_future,
                _,
            ) = identity_client.subscribe_to_create_keys_and_certificate_accepted(
                request=createkeysandcertificate_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.createkeysandcertificate_execution_accepted,
            )
            # Wait for subscription to succeed
            createkeysandcertificate_subscribed_accepted_future.result()

            print("Subscribing to CreateKeysAndCertificate Rejected topic...")
            (
                createkeysandcertificate_subscribed_rejected_future,
                _,
            ) = identity_client.subscribe_to_create_keys_and_certificate_rejected(
                request=createkeysandcertificate_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.createkeysandcertificate_execution_rejected,
            )
            # Wait for subscription to succeed
            createkeysandcertificate_subscribed_rejected_future.result()

            registerthing_subscription_request = (
                iotidentity.RegisterThingSubscriptionRequest(
                    template_name=TEMPLATE_NAME
                )
            )

            print("Subscribing to RegisterThing Accepted topic...")
            (
                registerthing_subscribed_accepted_future,
                _,
            ) = identity_client.subscribe_to_register_thing_accepted(
                request=registerthing_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.registerthing_execution_accepted,
            )
            # Wait for subscription to succeed
            registerthing_subscribed_accepted_future.result()

            print("Subscribing to RegisterThing Rejected topic...")
            (
                registerthing_subscribed_rejected_future,
                _,
            ) = identity_client.subscribe_to_register_thing_rejected(
                request=registerthing_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.registerthing_execution_rejected,
            )
            # Wait for subscription to succeed
            registerthing_subscribed_rejected_future.result()

            print("Publishing to CreateKeysAndCertificate...")
            publish_future = identity_client.publish_create_keys_and_certificate(
                request=iotidentity.CreateKeysAndCertificateRequest(),
                qos=mqtt.QoS.AT_LEAST_ONCE,
            )
            publish_future.add_done_callback(
                self.on_publish_create_keys_and_certificate
            )

            self.wait_for_create_keys_and_certificate_response()

            if self.create_keys_and_certificate_response is None:
                raise Exception(  # pylint: disable=W0719
                    "CreateKeysAndCertificate API did not succeed"
                )
            cert_own_token = (
                self.create_keys_and_certificate_response.certificate_ownership_token
            )
            register_thing_request = iotidentity.RegisterThingRequest(
                template_name=TEMPLATE_NAME,
                certificate_ownership_token=cert_own_token,
                parameters=json.loads(self.template_parameters),
            )

            print("Publishing to RegisterThing topic...")
            registerthing_publish_future = identity_client.publish_register_thing(
                register_thing_request, mqtt.QoS.AT_LEAST_ONCE
            )
            registerthing_publish_future.add_done_callback(
                self.on_publish_register_thing
            )

            self.wait_for_register_thing_response()

            # Disconnect
            print("Disconnecting...")
            disconnect_future = self.mqtt_connection.disconnect()
            disconnect_future.result()
            print("Disconnected!")
            success = True

        except Exception as exept:  # pylint: disable=W0718
            print(f"Exit with exception: {exept}")

        return success

    def send_vehicle_connection_request(self) -> None:
        mqtt_connection = mqtt_connection_builder.mtls_from_bytes(
            endpoint=self.iot_endpoint,
            port=REMOTE_PORT,
            cert_bytes=self.provisioned_credentials.certificate_pem
            if self.provisioned_credentials is not None
            else b"",
            pri_key_bytes=self.provisioned_credentials.private_key
            if self.provisioned_credentials is not None
            else b"",
            ca_bytes=self.claim_credentials.ca_certificate,
            on_connection_interrupted=self.on_connection_interrupted,
            on_connection_resumed=self.on_connection_resumed,
            # use IoT thing name  as a session ID
            client_id=self.connect_client_id,
            clean_session=False,
            keep_alive_secs=30,
            http_proxy_options=None,
        )
        print(
            f"Connecting to {self.iot_endpoint} with client ID {self.connect_client_id} ..."
        )
        connected_future = mqtt_connection.connect()

        # Wait for connection to be fully established.
        # Note that it's not necessary to wait, commands issued to the
        # mqtt_connection before its fully connected will simply be queued.
        # But this sample waits here so it's obvious when a connection
        # fails or succeeds.
        connected_future.result()
        print("Connected!")

        # publish our first message
        message = {
            "vin": self.vin,
            "certificate_id": self.provisioned_credentials.certificate_id
            if self.provisioned_credentials is not None
            else "",
        }
        message_json = json.dumps(message)
        pub_future, _ = mqtt_connection.publish(
            "vehicleactive/", message_json, mqtt.QoS.AT_MOST_ONCE
        )
        pub_future.result()

        # Disconnect
        print("Disconnecting...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")


if __name__ == "__main__":
    VIN = "KMHFG4JG1CA181127"
    add_vehicle_to_authorized_vehicles_table(
        vin=VIN,
        table_name=get_authorized_vehicles_table_name(),
    )

    provisioning = ProvisioningByClaim(vin=VIN)

    provisioning.send_vehicle_provisioning_request()
    provisioning.send_vehicle_connection_request()
