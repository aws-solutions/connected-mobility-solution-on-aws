// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import { I18n, Logger } from "@aws-amplify/core";
import { API } from "@aws-amplify/api";
import { ISimulation } from "../Shared/Interfaces";
import DeleteConfirm from "../Shared/DeleteConfirmation";
import { API_NAME } from "../../util/Utils";
import { Link } from "react-router-dom";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import Table from "react-bootstrap/Table";

interface IProps {
  simulations: ISimulation[];
  handleCheckboxSelect: Function;
  setSimulations: Function;
}

export default function TableData(props: IProps): React.JSX.Element {
  const logger = new Logger("Simulation Table Data");
  const [showDevices, setShowDevices] = useState(-1);
  const [deleteModalIndex, setDeleteModalIndex] = useState<number | null>(null);

  /**
   * deletes the given simulation from ddb and reloads the page
   * @param sim_id
   */
  const handleDelete = async (sim_id: string, index: number) => {
    try {
      await API.del(API_NAME, `/simulation/${sim_id}`, {});
      props.simulations.splice(index, 1);
      props.setSimulations([...props.simulations]);
    } catch (err) {
      logger.error(I18n.get("simulation.delete.error"), err);
      throw err;
    }
  };

  return (
    <tbody>
      {props.simulations.map((sim, i) => (
        <tr key={`${sim.sim_id}-${i}`}>
          <td>
            <Form.Check
              id="sim.id"
              type="checkbox"
              checked={sim.checked}
              onChange={(event) => {
                props.handleCheckboxSelect(event, i);
              }}
            ></Form.Check>
          </td>
          <td>{sim.name}</td>
          <td>{sim.stage}</td>
          <td>
            &nbsp;
            <Button
              className="button-theme button-rounded"
              size="sm"
              onClick={() => {
                setShowDevices(i);
              }}
            >
              <i className="bi bi-info-circle" /> {I18n.get("info")}
            </Button>
            <Modal
              show={showDevices === i}
              onHide={() => {
                setShowDevices(-1);
              }}
            >
              <Modal.Header closeButton>
                <Modal.Title>{sim.name}</Modal.Title>
              </Modal.Header>
              <Modal.Body>
                <Table className="form-table table-header" borderless>
                  <thead>
                    <tr>
                      <th>{I18n.get("device.types")}</th>
                      <th>{I18n.get("amount")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sim.devices.map((device, j) => (
                      <tr key={`${device.name}-${device.type_id}-${j}`}>
                        <td>{device.name}</td>
                        <td>{device.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Modal.Body>
            </Modal>
          </td>
          <td>{sim.runs}</td>
          <td>{sim.last_run ? sim.last_run : ""}</td>
          <td>
            <Link
              to={`/simulations/${sim.sim_id}`}
              state={{
                simulation: sim.sim_id,
              }}
            >
              <Button size="sm" className="button-theme" type="submit">
                <i className="bi bi-eye-fill" /> {I18n.get("view")}
              </Button>
            </Link>
            <Button
              size="sm"
              className="button-theme-alt"
              onClick={() => {
                setDeleteModalIndex(i);
              }}
            >
              <i className="bi bi-trash-fill" /> {I18n.get("delete")}
            </Button>
            <DeleteConfirm
              id={sim.sim_id}
              name={sim.name}
              delete={handleDelete}
              showModal={setDeleteModalIndex}
              show={deleteModalIndex === i}
              index={i}
            />
          </td>
        </tr>
      ))}
    </tbody>
  );
}
