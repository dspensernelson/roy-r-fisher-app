async function j(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // message is unchanged, so every existing caller keeps the sentence it
    // already showed. What is added is the little the startup screen needs to
    // tell one failure from another, and nothing more: the status line and the
    // server's own flag. Deliberately not the whole body, so no future caller
    // can reach through this and put server internals on a screen.
    const err = new Error(body.detail || res.statusText);
    err.status = res.status;
    err.stateUnreadable = body.state_unreadable === true;
    throw err;
  }
  return res.json();
}
export const listJobs = () => fetch("/api/jobs").then(j);
export const createJob = (name) =>
  fetch("/api/jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }).then(j);
export const jobDetail = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}`).then(j);
export const getManifest = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/manifest`).then(j);
export const putManifest = (name, m) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/manifest`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(m) }).then(j);
export const draftCaptions = (name, confirmed) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/captions${confirmed ? "?confirmed=true" : ""}`, { method: "POST" }).then(j);
export const build = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/build`, { method: "POST" }).then(j);
export const reveal = (name, file, what) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/reveal`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file, what }) }).then(j);
export const thumbUrl = (name, file) => `/api/jobs/${encodeURIComponent(name)}/thumb/${encodeURIComponent(file)}`;
export const jobFolders = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/folders`).then(j);
export const photoGroups = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/photo-groups`).then(j);
export const putPhotoGroup = (name, folder) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/photo-group`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ folder }) }).then(j);
export const classificationLabels = () => fetch("/api/classifications").then(j);
export const setClassifications = (name, files, label) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/classifications`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ files, label }) }).then(j);
export const setClassification = (name, file, label) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/classification`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file, label }) }).then(j);
export const clearClassification = (name, file) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/classification`, { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file }) }).then(j);
export const captionStyles = () => fetch("/api/caption-styles").then(j);
export const appVersion = () => fetch("/api/version").then(j);
export const captionEstimate = (name) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/caption-estimate`).then(j);
export const captionProgress = (name) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/caption-progress`).then(j);
export const markReviewed = (name, file) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/photos/${encodeURIComponent(file)}/reviewed`, { method: "POST" }).then(j);
export const markUnreviewed = (name, file) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/photos/${encodeURIComponent(file)}/unreviewed`, { method: "POST" }).then(j);
export const jobFacts = (name) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/facts`).then(j);
export const putJobFacts = (name, body) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/facts`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(j);
export const proposeName = (body) =>
  fetch("/api/intake/propose-name", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(j);
export const createIntake = (body) =>
  fetch("/api/intake", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(j);
export const getWorkspace = () => fetch("/api/workspace").then(j);
export const browseFolders = (path) => fetch(`/api/browse?path=${encodeURIComponent(path || "")}`).then(j);
export const getWorkspaceFolders = () => fetch("/api/workspace/folders").then(j);
export const putWorkspaceFolders = (active) =>
  fetch("/api/workspace/folders", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ active }) }).then(j);
export const getDemo = () => fetch("/api/demo").then(j);
export const resetDemo = () => fetch("/api/demo/reset", { method: "POST" }).then(j);
export const saveWorkspace = (path, acceptEmpty) =>
  fetch("/api/workspace", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path, accept_empty: !!acceptEmpty }) }).then(j);
export const forgetWorkspace = () => fetch("/api/workspace", { method: "DELETE" }).then(j);
export const cutPhoto = (name, file) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/photos/${encodeURIComponent(file)}/cut`, { method: "POST" }).then(j);
export const uncutPhoto = (name, file) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/photos/${encodeURIComponent(file)}/uncut`, { method: "POST" }).then(j);
export const clearCaptions = (name) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/captions/clear`, { method: "POST" }).then(j);
export const getSettings = () => fetch("/api/settings").then(j);
export const saveKey = (key) =>
  fetch("/api/settings/key", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) }).then(j);
export const removeKey = () => fetch("/api/settings/key", { method: "DELETE" }).then(j);
export const getSections = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/sections`).then(j);
export const putSections = (name, list) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/sections`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sections: list }) }).then(j);
export async function uploadPhotos(name, files) {
  const form = new FormData();
  [...files].forEach((f) => form.append("files", f));
  return fetch(`/api/jobs/${encodeURIComponent(name)}/photos`, { method: "POST", body: form }).then(j);
}
