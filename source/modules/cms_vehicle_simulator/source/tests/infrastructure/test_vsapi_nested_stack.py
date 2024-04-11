# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# AWS Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ...infrastructure.cms_vehicle_simulator_stack import CmsVehicleSimulatorStack


def test_vsapi_apigw_path_count(
    cms_vehicle_simulator_stack: CmsVehicleSimulatorStack,
) -> None:
    template = assertions.Template.from_stack(cms_vehicle_simulator_stack).to_json()
    paths = (
        template.get("Resources")  # type: ignore[union-attr]
        .get("RestAPI")
        .get("Properties")
        .get("DefinitionBody")
        .get("paths")
    )
    template_id_path_methods = list(paths.get("/template/{template_id}").keys())
    template_path_methods = list(paths.get("/template").keys())
    device_path_methods = list(paths.get("/device").keys())
    device_type_path_methods = list(paths.get("/device/type").keys())
    device_type_id_path_methods = list(
        paths.get("/device/type/{device_type_id}").keys()
    )
    simulation_path_methods = list(paths.get("/simulation").keys())
    simulation_id_path_methods = list(paths.get("/simulation/{simulation_id}").keys())
    assert len(paths.keys()) == 7
    assert template_id_path_methods.sort() == ["get", "delete", "options"].sort()
    assert template_path_methods.sort() == ["get", "post", "put", "options"].sort()
    assert device_path_methods.sort() == ["get", "options"].sort()
    assert device_type_path_methods.sort() == ["get", "post", "put", "options"].sort()
    assert device_type_id_path_methods.sort() == ["get", "delete", "options"].sort()
    assert simulation_path_methods.sort() == ["get", "post", "options"].sort()
    assert (
        simulation_id_path_methods.sort() == ["get", "put", "delete", "options"].sort()
    )


def test_vsapi_apigw_is_authorized(
    cms_vehicle_simulator_stack: CmsVehicleSimulatorStack,
) -> None:
    template = assertions.Template.from_stack(cms_vehicle_simulator_stack).to_json()
    api_security_definitions = (
        template.get("Resources")  # type: ignore[union-attr]
        .get("RestAPI")
        .get("Properties")
        .get("DefinitionBody")
        .get("securityDefinitions")
    )
    api_collection_authorizers = api_security_definitions.keys()

    paths = (
        template.get("Resources")  # type: ignore[union-attr]
        .get("RestAPI")
        .get("Properties")
        .get("DefinitionBody")
        .get("paths")
    )

    def check_api_is_authorized(api_uri: Dict[str, Any]) -> None:
        for http_method, http_method_properties in api_uri.items():
            if http_method == "options":
                continue
            http_method_authorizers = []
            for authorizer in http_method_properties["security"]:
                http_method_authorizers.extend(authorizer.keys())
            # each api should have atleast one authorizer
            assert len(http_method_authorizers) > 0
            # the authorizers for the api method should be a subset of the
            # authorizers defined for the api collection
            assert set(http_method_authorizers).issubset(api_collection_authorizers)

    api_uris = paths.values()
    for api_uri in api_uris:
        check_api_is_authorized(api_uri=api_uri)
