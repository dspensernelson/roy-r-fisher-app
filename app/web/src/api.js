async function j(res) {
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}
export const listJobs = () => fetch("/api/jobs").then(j);
export const createJob = (name) =>
  fetch("/api/jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }).then(j);
export const jobDetail = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}`).then(j);
export const getManifest = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/manifest`).then(j);
export const putManifest = (name, m) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/manifest`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(m) }).then(j);
export const draftCaptions = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/captions`, { method: "POST" }).then(j);
export const build = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/build`, { method: "POST" }).then(j);
export const thumbUrl = (name, file) => `/api/jobs/${encodeURIComponent(name)}/thumb/${encodeURIComponent(file)}`;
export const scanJob = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/scan`).then(j);
export const captionStyles = () => fetch("/api/caption-styles").then(j);
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
export const saveWorkspace = (path) =>
  fetch("/api/workspace", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path }) }).then(j);
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
export const captionPreview = (name) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/caption-preview`, { method: "POST" }).then(j);
export const getSections = (name) => fetch(`/api/jobs/${encodeURIComponent(name)}/sections`).then(j);
export const putSections = (name, list) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/sections`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sections: list }) }).then(j);
export async function uploadPhotos(name, files) {
  const form = new FormData();
  [...files].forEach((f) => form.append("files", f));
  return fetch(`/api/jobs/${encodeURIComponent(name)}/photos`, { method: "POST", body: form }).then(j);
}
