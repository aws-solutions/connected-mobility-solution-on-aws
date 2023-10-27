# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import getopt
import json
import re
import subprocess  # nosec
import sys
import traceback
from os.path import abspath, dirname, join
from pathlib import Path
from typing import Any, Dict

# This script generates a variety of different data model files for the
# Vehicle Signal Specification (VSS) https://github.com/COVESA/vehicle_signal_specification.
# It uses scripts provided by the vss-tools github repository (https://github.com/covesa/vss-tools/tree/e95d3f24b0cb161873dd53b39fe8ecbecfe8706c)
# to generate different file types and perform post processing steps needed
# to convert to a format consumable by the modules of Connected Mobility Solution on AWS.

# This script should be called as follows from the root directory of the solution:
# python ./deployment/generate_models.py [--review=<forked_vss_repo>]

OUTPUT_PATH = join(dirname(dirname(abspath(__file__))), "generated_models")


class GlueTranslator:
    @staticmethod
    def handle(payload: Dict[str, Any]) -> Dict[str, Any]:
        types = {
            "string": GlueTranslator._string,
            "float": GlueTranslator._float,
            "boolean": GlueTranslator._boolean,
            "uint8": GlueTranslator._int,
            "int8": GlueTranslator._int,
            "uint16": GlueTranslator._int,
            "int16": GlueTranslator._int,
            "uint32": GlueTranslator._int,
            "int32": GlueTranslator._int,
            "double": GlueTranslator._float,
            "string[]": GlueTranslator._string,
            "float[]": GlueTranslator._float,
            "boolean[]": GlueTranslator._boolean,
            "uint8[]": GlueTranslator._int,
            "int8[]": GlueTranslator._int,
            "uint16[]": GlueTranslator._int,
            "int16[]": GlueTranslator._int,
            "uint32[]": GlueTranslator._int,
            "int32[]": GlueTranslator._int,
            "double[]": GlueTranslator._float,
        }
        return types[payload["datatype"]](payload)

    @staticmethod
    def _string(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "string",
            "length": int(payload["description"].split("-character")[0])
            if "character" in payload["description"]
            else 20,
        }
        if payload.get("default"):
            ret["default"] = payload["default"]
        if payload.get("allowed"):
            ret["enum"] = payload["allowed"]

        return ret

    @staticmethod
    def _int(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "integer",
            "minimum": payload.get("min", 0),
            "maximum": payload.get("max", 10),
        }
        if payload.get("default"):
            ret["default"] = payload["default"]

        return ret

    @staticmethod
    def _boolean(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "boolean",
        }
        if payload.get("default"):
            ret["default"] = payload["default"]

        return ret

    @staticmethod
    def _float(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "number",
            "minimum": payload.get("min", 0),
            "maximum": payload.get("max", 100),
            "precision": payload.get("precision", 0.0001),
        }
        if payload.get("default"):
            ret["default"] = payload["default"]

        return ret


class SimTranslator:
    @staticmethod
    def handle(payload: Dict[str, Any]) -> Dict[str, Any]:
        types = {
            "string": SimTranslator._string,
            "float": SimTranslator._float,
            "boolean": SimTranslator._boolean,
            "uint8": SimTranslator._int,
            "int8": SimTranslator._int,
            "uint16": SimTranslator._int,
            "int16": SimTranslator._int,
            "uint32": SimTranslator._int,
            "int32": SimTranslator._int,
            "double": SimTranslator._float,
            "string[]": SimTranslator._string,
            "float[]": SimTranslator._float,
            "boolean[]": SimTranslator._boolean,
            "uint8[]": SimTranslator._int,
            "int8[]": SimTranslator._int,
            "uint16[]": SimTranslator._int,
            "int16[]": SimTranslator._int,
            "uint32[]": SimTranslator._int,
            "int32[]": SimTranslator._int,
            "double[]": SimTranslator._float,
        }
        return types[payload["datatype"]](payload)

    @staticmethod
    def _string(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "string",
            "length": int(payload["description"].split("-character")[0])
            if "character" in payload["description"]
            else 20,
        }
        if payload.get("default"):
            ret["default"] = payload["default"]
        if payload.get("allowed"):
            ret["type"] = "pickOne"
            ret["arr"] = payload["allowed"]
        if payload.get("name") == "timestamp":
            ret["type"] = "timestamp"

        return ret

    @staticmethod
    def _int(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "int",
            "minimum": int(payload.get("min", 0)),
            "maximum": int(payload.get("max", 10)),
        }
        if payload.get("default"):
            ret["default"] = payload["default"]

        return ret

    @staticmethod
    def _boolean(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "bool",
        }
        if payload.get("default"):
            ret["default"] = payload["default"]

        return ret

    @staticmethod
    def _float(payload: Dict[str, Any]) -> Dict[str, Any]:
        ret = {
            "type": "float",
            "minimum": int(payload.get("min", 0)),
            "maximum": int(payload.get("max", 100)),
            "precision": len(str(payload.get("precision", 0.0001)).split(".")),
        }
        if payload.get("default"):
            ret["default"] = payload["default"]

        return ret


class ScriptException(Exception):
    ...


def process_glue(vss_object: Dict[str, Any]) -> Dict[str, Any]:
    if vss_object.get("type") == "branch":
        branch = {
            key.lower(): process_glue(value)
            for key, value in vss_object["children"].items()
        }
        return {"type": "object", "properties": branch}

    return GlueTranslator.handle(vss_object)


def process_sim(vss_object: Dict[str, Any], key: str = "") -> Dict[str, Any]:
    if vss_object.get("type") == "branch":
        return {
            "type": "object",
            "name": (key or "").lower(),
            "payload": [process_sim(v, k) for k, v in vss_object["children"].items()],
        }

    vss_object.update({"name": key.lower()})
    field = SimTranslator.handle(vss_object)
    field["name"] = key.lower()
    return field


def process_schema(vss_schema_raw: str) -> str:
    replacements = [
        (
            r'([^\S\r\n]*)"""\n?[^\S\r\n]*(.+)\n?[^\S\r\n]*"""',
            r"\1# \2",
        ),  # Replaces """ """ comments with # comments
        (
            r"(\S+.+: )\[(.+)\]",
            r"\1\2",
        ),  # Removes array values from schema
        (r"type Query \{(|\n|\r|.)+?\}\n*", ""),  # Removes default query type
        (
            r"\n.+\n +timestamp: String\n",
            "",
        ),  # Removes timestamp fields
        (
            r"\n.+\n +unit: String\n",
            "",
        ),  # Removes unit fields
    ]

    result = vss_schema_raw
    for old, new in replacements:
        result = re.sub(old, new, result)

    return result


if __name__ == "__main__":
    repository = "https://github.com/COVESA/vehicle_signal_specification"  # pylint: disable=C0103

    opts, args = getopt.getopt(sys.argv[1:], "hr:", ["help", "repository="])
    for opt, arg in opts:
        if opt == "-h":
            print(
                "\n"
                + "Usage: python ./deployment/generate_models.py\n"
                + "Generate data models from VSS repository.\n"
                + "-h, --help: show help info\n"
                + "-r, --repository: alternative fork of vss repository to generate models from (defaults to https://github.com/COVESA/vehicle_signal_specification)"
                + "\n"
            )
            sys.exit()
        elif opt in ("-r", "--repository"):
            repository = arg

    try:
        Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
        with subprocess.Popen(  # nosec
            f"git clone --recurse-submodules {repository}".split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=OUTPUT_PATH,
        ) as process:
            output, error = process.communicate()
            if process.returncode != 0:
                raise ScriptException(
                    f"Failed to git clone. returncode: {process.returncode}, error: {str(error)}"
                )

        VSS_TOOLS_PATH = join(OUTPUT_PATH, "vehicle_signal_specification/vss-tools/")
        with subprocess.Popen(  # nosec
            "pipenv install --dev",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=VSS_TOOLS_PATH,
        ) as process:
            output, error = process.communicate()
            if process.returncode != 0:
                raise ScriptException(
                    f"Failed to install dependencies. returncode: {process.returncode}, error: {str(error)}"
                )

        with subprocess.Popen(  # nosec
            "python vspec2x.py --format json -I ../spec ../spec/VehicleSignalSpecification.vspec ../../vss.json",
            stdout=subprocess.PIPE,
            shell=True,
            cwd=VSS_TOOLS_PATH,
        ) as process:
            output, error = process.communicate()
            if process.returncode != 0:
                raise ScriptException(
                    f"Failed to generate model. returncode: {process.returncode}, error: {str(error)}"
                )

        with subprocess.Popen(  # nosec
            "python vspec2graphql.py ../spec/VehicleSignalSpecification.vspec ../../vss_types.graphql",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=VSS_TOOLS_PATH,
        ) as process:
            output, error = process.communicate()
            if process.returncode != 0:
                raise ScriptException(
                    f"Failed to generate schema. returncode: {process.returncode}, error: {str(error)}"
                )

        # Generate json files
        with open(join(OUTPUT_PATH, "vss.json"), "r", encoding="utf-8") as vss_json:
            vss = json.loads(vss_json.read())

        with open(
            join(OUTPUT_PATH, "glue_template.json"), "w", encoding="utf-8"
        ) as glue_file:
            glue_file.write(json.dumps(process_glue(vss["Vehicle"]), indent=2))

        with open(
            join(OUTPUT_PATH, "vss_default_template.json"), "w", encoding="utf-8"
        ) as sim_file:
            sim_payload = {
                "template_id": "vehicle",
                "payload": process_sim(vss["Vehicle"])["payload"],
            }
            sim_file.write(json.dumps(sim_payload, indent=2))

        # Generate graphql files
        with open(
            join(OUTPUT_PATH, "vss_types.graphql"), "r", encoding="utf-8"
        ) as schema_file:
            raw_vss_schema = schema_file.read()

        with open(
            join(OUTPUT_PATH, "vss_types.graphql"), "w", encoding="utf-8"
        ) as schema_file:
            schema_file.write(process_schema(raw_vss_schema))

    except ScriptException:
        traceback.print_exc()

    finally:
        with subprocess.Popen(  # nosec
            "rm -rf vehicle_signal_specification".split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=OUTPUT_PATH,
        ) as process:
            process.communicate()
