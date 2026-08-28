import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const fixtureUrl = new URL("./contract-fixtures.json", import.meta.url);
const fixture = JSON.parse(readFileSync(fixtureUrl, "utf8"));

const expectedIdentity = {
  manifest: "docforge.yaml",
  projectSchema: "docforge.project.v1",
  source: "document.md",
  docx: "build/document.docx",
  reviewMarkdown: "review/document.review.md",
  reviewMap: "review/document.review-map.json",
  workbenchProtocol: "docforge.workbench.v1",
  buildReportSchema: "docforge.build-report.v2",
};

assert.deepEqual(fixture.identity, expectedIdentity);

for (const [name, component] of Object.entries(fixture.components)) {
  assert.ok(component.owns.length > 0, `${name} must own at least one concern`);
  assert.equal(
    new Set(component.owns).size,
    component.owns.length,
    `${name} ownership must be unique`,
  );
  assert.ok(
    component.forbiddenDependencies.length > 0,
    `${name} must declare forbidden dependencies`,
  );
}

function evaluateCase(testCase) {
  if (
    testCase.manifest !== expectedIdentity.manifest ||
    testCase.schema !== expectedIdentity.projectSchema
  ) {
    return "rejected-project";
  }
  if (
    testCase.path.startsWith("/") ||
    testCase.path.includes("..") ||
    /^[a-z][a-z0-9+.-]*:/i.test(testCase.path)
  ) {
    return "rejected-path";
  }
  if (testCase.protocol !== expectedIdentity.workbenchProtocol) {
    return "rejected-protocol";
  }
  return "accepted";
}

for (const testCase of fixture.cases) {
  assert.equal(
    evaluateCase(testCase),
    testCase.expected,
    `${testCase.id} crossed the wrong component boundary`,
  );
}

const acceptedCases = fixture.cases.filter(
  (testCase) => evaluateCase(testCase) === "accepted",
);
assert.deepEqual(
  acceptedCases.map(({ id }) => id),
  ["general", "academic"],
);
assert.deepEqual(
  acceptedCases.map(({ documentType }) => documentType),
  ["general", "academic"],
);

console.log(
  JSON.stringify({
    status: "green",
    checkedCases: fixture.cases.map(({ id }) => id),
    acceptedPipeline: acceptedCases.map(({ id }) => id),
    identity: fixture.identity,
  }),
);
