"use strict";
const byId = (id) => document.getElementById(id);
let current = null;
function status(message, error = false) {
  const item = byId("status");
  item.textContent = message;
  item.className = error ? "error" : "notice";
}
async function api(path, options = {}) {
  const response = await fetch(new URL(path, window.location.origin).href, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!response.ok) {
    let message = "Não foi possível concluir a operação.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail))
        message = body.detail.map((x) => x.msg).join("; ");
    } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}
async function run(action) {
  try {
    await action();
  } catch (error) {
    status(error.message, true);
  }
}
function button(label, action, secondary = false) {
  const node = document.createElement("button");
  node.type = "button";
  node.textContent = label;
  if (secondary) node.className = "secondary";
  node.onclick = () => run(action);
  return node;
}
async function loadStores() {
  const stores = await api("/admin/stores");
  const list = byId("store-list");
  list.replaceChildren();
  if (!stores.length) list.textContent = "Sua primeira loja começa aqui.";
  for (const store of stores) {
    const row = document.createElement("div");
    row.className = "list-item";
    const name = document.createElement("span");
    name.textContent = store.name + (store.is_active ? "" : " · inativa");
    row.append(
      name,
      button("Gerenciar", () => loadStore(store.id), true),
    );
    list.append(row);
  }
}
async function loadStore(id) {
  current = await api(`/admin/stores/${id}`);
  byId("store-detail").hidden = false;
  byId("detail-title").textContent = current.store.name;
  byId("edit-name").value = current.store.name;
  byId("edit-description").value = current.store.description || "";
  byId("edit-active").checked = current.store.is_active;
  byId("private-link").replaceChildren();
  renderLinks();
  renderPlates();
}
function renderLinks() {
  const root = byId("link-forms");
  root.replaceChildren();
  for (const [key, label] of [
    ["google", "Google"],
    ["whatsapp", "WhatsApp"],
    ["instagram", "Instagram"],
  ]) {
    const saved = current.links.find((x) => x.destination === key);
    const form = document.createElement("form");
    const title = document.createElement("label");
    title.textContent = label;
    title.htmlFor = `url-${key}`;
    const input = document.createElement("input");
    input.id = `url-${key}`;
    input.type = "url";
    input.required = true;
    input.placeholder = "https://";
    input.value = saved?.url || "";
    const active = document.createElement("input");
    active.type = "checkbox";
    active.checked = saved?.is_active ?? true;
    const activeLabel = document.createElement("label");
    activeLabel.append(active, document.createTextNode(" Canal ativo"));
    const submit = document.createElement("button");
    submit.textContent = "Salvar " + label;
    submit.className = "secondary";
    form.append(title, input, activeLabel, submit);
    form.onsubmit = (e) => {
      e.preventDefault();
      run(async () => {
        await api(`/admin/stores/${current.store.id}/links/${key}`, {
          method: "PUT",
          body: JSON.stringify({ url: input.value, is_active: active.checked }),
        });
        status("Canal salvo.");
      });
    };
    root.append(form);
  }
}
function renderPlates() {
  const list = byId("plate-list");
  list.replaceChildren();
  for (const plate of current.plates) {
    const row = document.createElement("div");
    row.className = "list-item";
    const text = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = plate.name || "Sem nome";
    const url = document.createElement("p");
    url.className = "private-url";
    url.textContent = plate.url;
    text.append(name, url);
    const actions = document.createElement("div");
    actions.className = "actions";
    const page = document.createElement("a");
    page.className = "button secondary";
    page.href = plate.url;
    page.target = "_blank";
    page.rel = "noopener noreferrer";
    page.textContent = "Abrir página";
    const qr = document.createElement("a");
    qr.className = "button secondary";
    qr.href = `/admin/plates/${plate.id}/qr.png`;
    qr.textContent = "Baixar QR";
    actions.append(
      page,
      qr,
      button(
        plate.is_active ? "Desativar" : "Ativar",
        async () => {
          await api(`/admin/plates/${plate.id}`, {
            method: "PATCH",
            body: JSON.stringify({
              name: plate.name,
              is_active: !plate.is_active,
            }),
          });
          await loadStore(current.store.id);
          status("Placa atualizada.");
        },
        true,
      ),
    );
    row.append(text, actions);
    list.append(row);
  }
}
byId("new-store").onsubmit = (e) => {
  e.preventDefault();
  run(async () => {
    const store = await api("/stores", {
      method: "POST",
      body: JSON.stringify({
        name: byId("new-name").value,
        description: byId("new-description").value || null,
      }),
    });
    e.target.reset();
    await loadStores();
    await loadStore(store.id);
    status("Loja criada. Configure os canais e crie a placa.");
  });
};
byId("edit-store").onsubmit = (e) => {
  e.preventDefault();
  run(async () => {
    await api(`/admin/stores/${current.store.id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: byId("edit-name").value,
        description: byId("edit-description").value || null,
        logo_url: current.store.logo_url,
        is_active: byId("edit-active").checked,
      }),
    });
    await loadStores();
    await loadStore(current.store.id);
    status("Loja atualizada.");
  });
};
byId("plate-form").onsubmit = (e) => {
  e.preventDefault();
  run(async () => {
    await api("/admin/plates", {
      method: "POST",
      body: JSON.stringify({
        store_id: current.store.id,
        name: byId("plate-name").value || null,
      }),
    });
    e.target.reset();
    await loadStore(current.store.id);
    status("Placa criada. Baixe o QR Code ou copie a URL para a NFC.");
  });
};
byId("logo-form").onsubmit = (e) => {
  e.preventDefault();
  run(async () => {
    const body = new FormData();
    body.append("file", byId("logo-file").files[0]);
    await api(`/admin/stores/${current.store.id}/logo`, {
      method: "POST",
      body,
    });
    await loadStore(current.store.id);
    status("Logo salvo.");
  });
};
byId("rotate-token").onclick = () =>
  run(async () => {
    if (
      current.store.has_metrics_link &&
      !confirm("Gerar outro link invalida o anterior. Continuar?")
    )
      return;
    const result = await api(
      `/admin/stores/${current.store.id}/metrics-token`,
      { method: "POST" },
    );
    current.store.has_metrics_link = true;
    const link = document.createElement("a");
    link.href = result.url;
    link.textContent = result.url;
    link.rel = "noreferrer";
    byId("private-link").replaceChildren(link);
    status(
      "Link gerado. Copie agora e envie à loja; ele não será exibido novamente.",
    );
  });
byId("revoke-token").onclick = () =>
  run(async () => {
    if (!confirm("Revogar o acesso da loja às métricas?")) return;
    await api(`/admin/stores/${current.store.id}/metrics-token`, {
      method: "DELETE",
    });
    current.store.has_metrics_link = false;
    byId("private-link").replaceChildren();
    status("Acesso revogado.");
  });
run(loadStores);
