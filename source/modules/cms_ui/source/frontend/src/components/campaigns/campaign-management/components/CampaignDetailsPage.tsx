// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  AppLayout,
  Button,
  Container,
  Flashbar,
  Header,
  KeyValuePairs,
  SpaceBetween,
} from "@cloudscape-design/components";
import { ReactNode, useEffect, useState, useContext } from "react";
import { ApiContext } from "@/api/provider";
import {
  CampaignItem,
  GetCampaignCommand,
} from "@com.cms.fleetmanagement/api-client";

export function CampaignDetailsPage({
  campaignName,
  onDeleteInit,
  notifications,
}: any) {
  const [campaign, setCampaign] = useState<CampaignItem>();

  const api = useContext(ApiContext);

  const fetchCampaign = async (campaignName: string) => {
    const input = { name: campaignName };
    const cmd = new GetCampaignCommand(input);
    const output = await api.client.send(cmd);
    setCampaign(output);
  };

  useEffect(() => {
    async function getCampaign() {
      await fetchCampaign(campaignName);
    }
    getCampaign();
  }, [window.location.hash]);

  return (
    <AppLayout
      content={
        <SpaceBetween size="m">
          <Header
            variant="h1"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button disabled={true} onClick={onDeleteInit}>
                  Delete
                </Button>
              </SpaceBetween>
            }
          >
            {campaign?.name}
          </Header>
          <SpaceBetween size="l">
            <Container header={<Header variant="h2">Campaign details</Header>}>
              <CampaignDetails campaign={campaign} />
            </Container>
          </SpaceBetween>
        </SpaceBetween>
      }
      notifications={<Flashbar items={notifications} stackItems={true} />}
      navigationOpen={false}
      navigationHide={true}
      toolsHide={true}
    />
  );
}

export function CampaignDetails({
  campaign,
}: {
  campaign: CampaignItem | undefined;
}): ReactNode {
  if (!campaign) {
    return;
  }
  return (
    <KeyValuePairs
      columns={3}
      items={[
        {
          type: "group",
          items: [
            {
              label: "Name",
              value: campaign.name,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "Status",
              value: campaign.status,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "Target ARN",
              value: campaign.targetId,
            },
          ],
        },
      ]}
    />
  );
}
