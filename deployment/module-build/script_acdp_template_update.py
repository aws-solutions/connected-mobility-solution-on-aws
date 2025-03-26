# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import argparse
import os
import traceback
from typing import Any, Dict, List, cast
from urllib.parse import urljoin

# Third Party Libraries
import yaml
from yaml.loader import SafeLoader

module_name = os.environ["MODULE_NAME"]
module_description = os.environ["MODULE_DESCRIPTION"]
global_asset_bucket = os.environ["GLOBAL_ASSET_BUCKET_NAME"]
global_asset_bucket_region = os.environ["GLOBAL_ASSET_BUCKET_REGION"]
s3_asset_key_prefix = os.environ["S3_ASSET_KEY_PREFIX"]
stack_template_name = os.environ["STACK_TEMPLATE_NAME"]

p = argparse.ArgumentParser()
p.add_argument("--component-template-path", default="./.acdp/template.yaml")
p.add_argument("--mkdocs-yml-path", default="./mkdocs.yml")
p.add_argument(
    "--component-template-output-path",
    default=f"deployment/regional-s3-assets/backstage/entities/templates/{module_name}.template.yaml",
)
p.add_argument(
    "--mkdocs-yml-output-path",
    default=f"{os.environ.get('STAGING_DIST_DIR', 'deployment/staging')}/mkdocs/mkdocs.yml",
)


# Custom constructor to replace environment variables (denoted by !ENV tag) with value from actual os.environ
def env_constructor(loader: SafeLoader, node: yaml.Node) -> str:
    value = str(loader.construct_scalar(cast(yaml.ScalarNode, node)))
    return os.environ[value]


yaml.add_constructor(tag="!ENV", constructor=env_constructor, Loader=SafeLoader)


def generate_s3_https_url(
    bucket_name: str, region: str, key_prefix: str, key: str
) -> str:
    if region == "us-east-1":  # For us-east-1, the region is omitted in the URL
        bucket_url = f"https://{bucket_name}.s3.amazonaws.com"
    else:
        bucket_url = f"https://{bucket_name}.s3.{region}.amazonaws.com"

    url_with_prefix = urljoin(bucket_url, key_prefix)
    full_url = urljoin(url_with_prefix, key)
    return full_url


def set_nested_json_key_value(
    json: Dict[str, Any], path: List[str], value: Any
) -> None:
    ptr = json
    for index, key in enumerate(path):
        if index == len(path) - 1:
            ptr[key] = value
        elif key not in ptr:
            ptr[key] = {}
        ptr = ptr[key]


def update_template(
    component_template_path: str, component_template_output_path: str
) -> None:
    with open(component_template_path, "r", encoding="utf-8") as stream:
        try:
            template = yaml.safe_load(stream)
        except yaml.YAMLError:
            print(f"Error parsing {component_template_path}")
            print(traceback.format_exc())
            return

    template["metadata"]["name"] = module_name
    template["metadata"]["description"] = module_description

    for index, form_page in enumerate(template["spec"]["parameters"]):
        if form_page["properties"].get("componentId"):
            set_nested_json_key_value(
                json=template["spec"]["parameters"][index],
                path=["properties", "componentId", "default"],
                value=module_name,
            )
        if form_page["properties"].get("description"):
            set_nested_json_key_value(
                json=template["spec"]["parameters"][index],
                path=["properties", "description", "default"],
                value=module_description,
            )

    for index, step in enumerate(template["spec"]["steps"]):
        if step["action"] == "aws:s3:catalog:write":
            set_nested_json_key_value(
                json=template["spec"]["steps"][index],
                path=["input", "entity", "metadata", "labels", "templateName"],
                value=module_name,
            )
            set_nested_json_key_value(
                json=template["spec"]["steps"][index],
                path=[
                    "input",
                    "entity",
                    "metadata",
                    "annotations",
                    "backstage.io/techdocs-entity",
                ],
                value=f"component:default/{module_name}-docs",
            )
        elif step["action"] == "aws:acdp:configure":
            for action_index, action_input in enumerate(
                step["input"]["buildParameters"]
            ):
                if action_input["name"] == "CFN_TEMPLATE_URL":
                    cfn_s3_url = generate_s3_https_url(
                        bucket_name=global_asset_bucket,
                        region=global_asset_bucket_region,
                        key_prefix=s3_asset_key_prefix,
                        key=f"{module_name}/{stack_template_name}",
                    )
                    set_nested_json_key_value(
                        json=template["spec"]["steps"][index]["input"][
                            "buildParameters"
                        ][action_index],
                        path=["value"],
                        value=cfn_s3_url,
                    )

    with open(component_template_output_path, "w", encoding="utf-8") as stream:
        yaml.dump(template, stream, width=150, indent=2)


def update_mkdocs_yml(
    mkdocs_yml_path: str,
    mkdocs_yml_output_path: str,
) -> None:
    with open(mkdocs_yml_path, "r", encoding="utf-8") as stream:
        try:
            mkdocs_yml = yaml.safe_load(stream)
        except yaml.YAMLError:
            print(f"Error parsing {mkdocs_yml_path}")
            print(traceback.format_exc())
            return

    with open(mkdocs_yml_output_path, "w", encoding="utf-8") as stream:
        yaml.dump(mkdocs_yml, stream, width=150, indent=2)


if __name__ == "__main__":
    args = p.parse_args()
    update_template(
        component_template_path=args.component_template_path,
        component_template_output_path=args.component_template_output_path,
    )

    update_mkdocs_yml(
        mkdocs_yml_path=args.mkdocs_yml_path,
        mkdocs_yml_output_path=args.mkdocs_yml_output_path,
    )
