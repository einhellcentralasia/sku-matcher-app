import test from "node:test";
import assert from "node:assert/strict";

import {
  getGitHubUpdateConfig,
  parseSinceTimestamp,
  summarizeOverallState,
  summarizeWorkflowRun,
} from "../functions/lib/github-update.js";

test("uses sku-matcher repository defaults", () => {
  assert.deepEqual(getGitHubUpdateConfig(), {
    apiBaseUrl: "https://api.github.com",
    apiVersion: "2022-11-28",
    userAgent: "sku-matcher-app-cloudflare-update",
    owner: "einhellcentralasia",
    repo: "sku-matcher-app",
    ref: "main",
    workflowId: "sync-sharepoint-mapping.yml",
  });
});

test("reports pending dispatch before GitHub exposes the run", () => {
  const result = summarizeWorkflowRun(
    "sync-sharepoint-mapping.yml",
    [],
    { value: Date.parse("2026-09-01T10:00:00.000Z") },
  );
  assert.equal(result.state, "pending_dispatch");
  assert.equal(summarizeOverallState([result]), "running");
});

test("reports in-progress and successful workflow states", () => {
  const since = { value: Date.parse("2026-09-01T10:00:00.000Z") };
  const running = summarizeWorkflowRun(
    "sync-sharepoint-mapping.yml",
    [{ status: "in_progress", created_at: "2026-09-01T10:00:02.000Z" }],
    since,
  );
  const success = summarizeWorkflowRun(
    "sync-sharepoint-mapping.yml",
    [
      {
        status: "completed",
        conclusion: "success",
        created_at: "2026-09-01T10:00:02.000Z",
      },
    ],
    since,
  );
  assert.equal(running.state, "in_progress");
  assert.equal(summarizeOverallState([running]), "running");
  assert.equal(success.state, "success");
  assert.equal(summarizeOverallState([success]), "success");
});

test("reports non-successful completed runs as failures", () => {
  const result = summarizeWorkflowRun(
    "sync-sharepoint-mapping.yml",
    [
      {
        status: "completed",
        conclusion: "cancelled",
        created_at: "2026-09-01T10:00:02.000Z",
      },
    ],
    { value: Date.parse("2026-09-01T10:00:00.000Z") },
  );
  assert.equal(result.state, "failure");
  assert.equal(summarizeOverallState([result]), "failure");
});

test("validates the status timestamp", () => {
  assert.equal(
    parseSinceTimestamp("https://example.test/api/update-status?since=2026-09-01T10%3A00%3A00Z").iso,
    "2026-09-01T10:00:00.000Z",
  );
  assert.throws(
    () => parseSinceTimestamp("https://example.test/api/update-status?since=bad"),
    /Invalid since timestamp/,
  );
});
