import React from "react";
import { render } from "@testing-library/react";

import Layout from "../components/Layout";
import { TestWrapper } from "./utils/testWrapper";


test("renders layout without crashing", () => {
  render(
    <TestWrapper>
      <Layout>
        <div>Test</div>
      </Layout>
    </TestWrapper>,
  );
});


