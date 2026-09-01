import {
  getGitHubTriggerToken,
  getGitHubUpdateConfig,
  githubHeaders,
  jsonResponse,
} from "../lib/github-update.js";

async function dispatchWorkflow(token, config) {
  const response = await fetch(
    `${config.apiBaseUrl}/repos/${config.owner}/${config.repo}/actions/workflows/${config.workflowId}/dispatches`,
    {
      method: "POST",
      headers: githubHeaders(config, token, true),
      body: JSON.stringify({ ref: config.ref }),
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Failed to dispatch ${config.workflowId}: ${response.status} ${response.statusText} ${errorText}`,
    );
  }
}

export async function onRequestPost(context) {
  try {
    const config = getGitHubUpdateConfig(context.env);
    const token = getGitHubTriggerToken(context.env);
    // Include a small clock-skew window because workflow_dispatch does not return a run id.
    const startedAt = new Date(Date.now() - 5000).toISOString();
    await dispatchWorkflow(token, config);

    return jsonResponse({
      ok: true,
      message: "SKU mapping update dispatched.",
      updateSession: {
        startedAt,
        workflow: config.workflowId,
      },
    });
  } catch (error) {
    return jsonResponse(
      {
        ok: false,
        error: error instanceof Error ? error.message : "Failed to start data update.",
      },
      500,
    );
  }
}
