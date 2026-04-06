import assert from "node:assert/strict";

const apiUrl = process.env.SMOKE_API_URL;
const webUrl = process.env.SMOKE_WEB_URL;

assert.ok(apiUrl, "SMOKE_API_URL is required");
assert.ok(webUrl, "SMOKE_WEB_URL is required");

function escapeRegex(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function assertContains(text, expected, context) {
  assert.match(text, new RegExp(escapeRegex(expected), "i"), `${context} missing "${expected}"`);
}

function assertAnyMatch(items, predicate, context) {
  assert.ok(items.some(predicate), context);
}

async function readText(url) {
  const response = await fetch(url, { cache: "no-store" });
  assert.equal(response.status, 200, `Expected 200 from ${url}`);
  return await response.text();
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  assert.equal(response.ok, true, `Expected success from ${url}`);
  return await response.json();
}

async function getJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  assert.equal(response.status, 200, `Expected 200 from ${url}`);
  return await response.json();
}

async function run() {
  const dashboardHtml = await readText(`${webUrl}/dashboard`);
  assertContains(dashboardHtml, "Projects", "dashboard");
  assertContains(dashboardHtml, "ThreadLite", "dashboard");

  const manufacturingSeed = await postJson(`${apiUrl}/api/seed/manufacturing-demo`, {});
  const personalSeed = await postJson(`${apiUrl}/api/seed/personal-demo`, {});
  const manufacturing = await getJson(`${apiUrl}/api/projects/${manufacturingSeed.project_id}`);
  const personal = await getJson(`${apiUrl}/api/projects/${personalSeed.project_id}`);

  const profiles = [
    {
      project: manufacturing,
      requirementSave: "Save Specification",
      blockSave: "Save Component",
      testSave: "Save Quality Check",
      cockpitTokens: ["Recommended workflow", "Specifications", "Components", "Quality Checks"],
      requirementToken: "Describe the product specification or quality constraint",
      blockToken: "Describe this part, assembly, or production station",
      testToken: "Describe the inspection procedure and acceptance criteria",
      requirementSectionKey: "MFG-SPEC-001",
      blockSectionName: "Packaging Line",
      componentSectionName: "Fill Head Assembly",
      testSectionTitle: "Fill Accuracy Check",
    },
    {
      project: personal,
      requirementSave: "Save Goal",
      blockSave: "Save Element",
      testSave: "Save Verification",
      cockpitTokens: ["Recommended workflow", "Goals", "Elements", "Verifications"],
      requirementToken: "Describe the goal or constraint for this project",
      blockToken: "Describe this device, service, or system element",
      testToken: "Describe how you will check this element is working correctly",
      requirementSectionKey: "HOME-GOAL-001",
      blockSectionName: "Home Network System",
      componentSectionName: "Backup Storage Node",
      testSectionTitle: "Overnight Backup Check",
    },
  ];

  for (const profile of profiles) {
    const { project } = profile;

    const homeHtml = await readText(`${webUrl}/projects/${project.id}`);
    assertContains(homeHtml, project.code, `project ${project.code}`);
    assertContains(homeHtml, project.name, `project ${project.code}`);
    for (const token of profile.cockpitTokens) {
      assertContains(homeHtml, token, `project ${project.code}`);
    }

    const requirementsForm = await readText(`${webUrl}/requirements/new?project=${project.id}`);
    assertContains(requirementsForm, profile.requirementSave, `requirements form ${project.code}`);
    assertContains(requirementsForm, profile.requirementToken, `requirements form ${project.code}`);

    const blocksForm = await readText(`${webUrl}/blocks/new?project=${project.id}`);
    assertContains(blocksForm, profile.blockSave, `blocks form ${project.code}`);
    assertContains(blocksForm, profile.blockToken, `blocks form ${project.code}`);

    const testsForm = await readText(`${webUrl}/test-cases/new?project=${project.id}`);
    assertContains(testsForm, profile.testSave, `tests form ${project.code}`);
    assertContains(testsForm, profile.testToken, `tests form ${project.code}`);

    const requirements = await getJson(`${apiUrl}/api/requirements?project_id=${project.id}`);
    assertAnyMatch(requirements, (item) => item.key === profile.requirementSectionKey, `requirements api ${project.code}`);

    const blocks = await getJson(`${apiUrl}/api/blocks?project_id=${project.id}`);
    assertAnyMatch(blocks, (item) => item.name === profile.blockSectionName, `blocks api ${project.code}`);

    const components = await getJson(`${apiUrl}/api/projects/${project.id}/components`);
    assertAnyMatch(components, (item) => item.name === profile.componentSectionName, `components api ${project.code}`);

    const tests = await getJson(`${apiUrl}/api/test-cases?project_id=${project.id}`);
    assertAnyMatch(tests, (item) => item.title === profile.testSectionTitle, `tests api ${project.code}`);

    await readText(`${webUrl}/projects/${project.id}/requirements`);
    await readText(`${webUrl}/projects/${project.id}/blocks`);
    await readText(`${webUrl}/projects/${project.id}/tests`);
  }

  console.log("Frontend smoke checks passed.");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
