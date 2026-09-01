const DEFAULT_GITHUB_API_BASE_URL = "https://api.github.com";
const DEFAULT_GITHUB_API_VERSION = "2022-11-28";
const DEFAULT_GITHUB_USER_AGENT = "sku-matcher-app-cloudflare-update";
const DEFAULT_GITHUB_OWNER = "einhellcentralasia";
const DEFAULT_GITHUB_REPO = "sku-matcher-app";
const DEFAULT_GITHUB_REF = "main";
const DEFAULT_GITHUB_WORKFLOW_ID = "sync-sharepoint-mapping.yml";

function configuredValue(env, name, fallback) {
  const value = typeof env?.[name] === "string" ? env[name].trim() : "";
  return value || fallback;
}

export function getGitHubUpdateConfig(env = {}) {
  return {
    apiBaseUrl: DEFAULT_GITHUB_API_BASE_URL,
    apiVersion: DEFAULT_GITHUB_API_VERSION,
    userAgent: configuredValue(env, "GITHUB_API_USER_AGENT", DEFAULT_GITHUB_USER_AGENT),
    owner: configuredValue(env, "GITHUB_REPO_OWNER", DEFAULT_GITHUB_OWNER),
    repo: configuredValue(env, "GITHUB_REPO_NAME", DEFAULT_GITHUB_REPO),
    ref: configuredValue(env, "GITHUB_REPO_REF", DEFAULT_GITHUB_REF),
    workflowId: configuredValue(
      env,
      "GITHUB_UPDATE_WORKFLOW_ID",
      DEFAULT_GITHUB_WORKFLOW_ID,
    ),
  };
}

export function getGitHubTriggerToken(env = {}) {
  const token = typeof env.GITHUB_ACTIONS_TRIGGER_TOKEN === "string"
    ? env.GITHUB_ACTIONS_TRIGGER_TOKEN.trim()
    : "";
  if (!token) {
    throw new Error("Missing Cloudflare secret GITHUB_ACTIONS_TRIGGER_TOKEN.");
  }
  return token;
}

export function githubHeaders(config, token, includeContentType = false) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "User-Agent": config.userAgent,
    "X-GitHub-Api-Version": config.apiVersion,
    ...(includeContentType ? { "Content-Type": "application/json" } : {}),
  };
}

export function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

export function parseSinceTimestamp(requestUrl) {
  const value = new URL(requestUrl).searchParams.get("since");
  if (!value) {
    throw new Error("Missing required query parameter: since");
  }
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) {
    throw new Error("Invalid since timestamp.");
  }
  return {
    iso: new Date(timestamp).toISOString(),
    value: timestamp,
  };
}

export function summarizeWorkflowRun(workflowId, workflowRuns, sinceTimestamp) {
  const matchedRun = workflowRuns.find((run) => {
    const createdAt = Date.parse(run?.created_at ?? "");
    return Number.isFinite(createdAt) && createdAt >= sinceTimestamp.value;
  });

  if (!matchedRun) {
    return {
      workflow: workflowId,
      state: "pending_dispatch",
    };
  }

  return {
    workflow: workflowId,
    state:
      matchedRun.status === "completed"
        ? matchedRun.conclusion === "success"
          ? "success"
          : "failure"
        : matchedRun.status,
    status: matchedRun.status,
    conclusion: matchedRun.conclusion,
    runId: matchedRun.id,
    runNumber: matchedRun.run_number,
    htmlUrl: matchedRun.html_url,
    createdAt: matchedRun.created_at,
    updatedAt: matchedRun.updated_at,
  };
}

export function summarizeOverallState(workflows) {
  if (workflows.some((workflow) => workflow.state === "failure")) {
    return "failure";
  }
  if (workflows.every((workflow) => workflow.state === "success")) {
    return "success";
  }
  return "running";
}
