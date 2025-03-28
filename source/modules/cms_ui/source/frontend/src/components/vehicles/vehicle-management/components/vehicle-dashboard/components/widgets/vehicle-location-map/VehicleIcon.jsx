// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { memo } from "react";

const VehicleIcon = ({ size, color = "#000" }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      height={size}
      width={size}
      viewBox="0 0 24 24"
    >
      <rect fill="white" x="4.364" y="9.354" width="15.784" height="7.564" />
      <path
        fill={color}
        d="M 5.76 1.82 L 18.82 1.82 C 19.925 1.82 20.82 2.715 20.82 3.82 L 20.82 11.95 L 21.15 11.95 C 21.32 11.95 21.46 12.35 21.46 12.85 L 21.46 14.31 C 21.46 14.81 21.32 15.16 21.15 15.16 L 20.82 15.16 L 20.82 18.67 C 20.82 19.407 20.422 20.05 19.83 20.397 C 19.835 20.447 19.836 20.498 19.83 20.55 L 19.83 21.79 C 19.871 22.164 19.595 22.498 19.22 22.53 L 18.06 22.53 C 17.679 22.478 17.409 22.132 17.45 21.75 L 17.45 20.67 L 7.2 20.67 L 7.2 21.79 C 7.235 22.166 6.956 22.498 6.58 22.53 L 5.42 22.53 C 5.039 22.478 4.769 22.132 4.81 21.75 L 4.81 20.55 C 4.806 20.509 4.805 20.469 4.807 20.429 C 4.183 20.091 3.76 19.43 3.76 18.67 L 3.76 15.16 L 3.51 15.16 C 3.34 15.16 3.2 14.76 3.2 14.26 L 3.2 12.85 C 3.2 12.35 3.34 11.95 3.51 11.95 L 3.76 11.95 L 3.76 3.82 C 3.76 2.715 4.655 1.82 5.76 1.82 Z M 4.78 11.56 L 4.78 14.23 C 4.78 15.335 5.675 16.23 6.78 16.23 L 17.79 16.23 C 18.895 16.23 19.79 15.335 19.79 14.23 L 19.79 11.56 C 19.79 10.455 18.895 9.56 17.79 9.56 L 6.78 9.56 C 5.675 9.56 4.78 10.455 4.78 11.56 Z M 6.28 18.14 C 5.452 18.14 4.78 18.48 4.78 18.9 C 4.78 19.32 5.452 19.66 6.28 19.66 C 7.108 19.66 7.78 19.32 7.78 18.9 C 7.78 18.48 7.108 18.14 6.28 18.14 Z M 18.3 18.13 C 17.472 18.13 16.8 18.47 16.8 18.89 C 16.8 19.31 17.472 19.65 18.3 19.65 C 19.128 19.65 19.8 19.31 19.8 18.89 C 19.8 18.47 19.128 18.13 18.3 18.13 Z"
      />
    </svg>
  );
};

export default memo(VehicleIcon);
