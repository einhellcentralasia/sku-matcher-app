import {
  getGitHubTriggerToken,
  getGitHubUpdateConfig,
  githubHeaders,
  jsonResponse,
  parseSinceTimestamp,
  summarizeOverallState,
  summarizeWorkflowRun,
} from "../lib/github-update.js";

async function listWorkflowRuns(token, config) {
  const url = new URL(
    `${config.apiBaseUrl}/repos/${config.owner}/${config.repo}/actions/workflows/${config.workflowId}/runs`,
  );
  url.searchParams.set("event", "workflow_dispatch");
  url.searchParams.set("branch", config.ref);
  url.searchParams.set("per_page", "20");

  const response = await fetch(url, {
    headers: githubHeaders(config, token),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Failed to fetch workflow runs: ${response.status} ${response.statusText} ${errorText}`,
    );
  }
  const payload = await response.json();
  return Array.isArray(payload.workflow_runs) ? payload.workflow_runs : [];
}

export async function onRequestGet(context) {
  try {
    const config = getGitHubUpdateConfig(context.env);
    const token = getGitHubTriggerToken(context.env);
    const sinceTimestamp = parseSinceTimestamp(context.request.url);
    const workflow = summarizeWorkflowRun(
      config.workflowId,
      await listWorkflowRuns(token, config),
      sinceTimestamp,
    );

    return jsonResponse({
      ok: true,
      state: summarizeOverallState([workflow]),
      since: sinceTimestamp.iso,
      workflow,
    });
  } catch (error) {
    return jsonResponse(
      {
        ok: false,
        error: error instanceof Error ? error.message : "Failed to load update status.",
      },
      500,
    );
  }
}
