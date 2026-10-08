"use strict";

// Shared image archive for the News and Pushback pages.
// Each page has its own manifest in assets/documents/<collection>/manifest.json.
const collectionName = document.body.dataset.collection;
const validCollections = new Set(["news", "pushback"]);
if (!validCollections.has(collectionName)) {
    throw new Error("Unknown document collection.");
}

const basePath = `../assets/documents/${collectionName}/`;
const countElement = document.getElementById("document-count");
const emptyElement = document.getElementById("archive-empty");
const groupsElement = document.getElementById("document-groups");
const modal = document.getElementById("document-modal");
const modalImage = document.getElementById("modal-image");
const modalTitle = document.getElementById("modal-title");
const modalLink = document.getElementById("modal-full-link");
const closeButton = document.getElementById("modal-close");
let allDocuments = [];
let currentIndex = 0;
let returnFocusElement = null;

function pageLabel(item) {
    return Number.isInteger(item.page) && item.page > 0
        ? `Page ${item.page}`
        : "Document";
}

function documentTitle(item) {
    return item.title || "Source document";
}

function createDocumentCard(item, index) {
    const button = document.createElement("button");
    button.className = "document-card";
    button.type = "button";
    button.setAttribute("aria-label", `Open ${documentTitle(item)}, ${pageLabel(item)}`);

    const imageWrap = document.createElement("div");
    imageWrap.className = "document-thumb-wrap";
    const image = document.createElement("img");
    image.src = basePath + "thumbs/" + item.thumbnail_filename;
    image.alt = `${documentTitle(item)}: ${pageLabel(item)}`;
    image.loading = "lazy";
    imageWrap.appendChild(image);

    const info = document.createElement("div");
    info.className = "document-card-info";
    const name = document.createElement("strong");
    name.textContent = pageLabel(item);
    const action = document.createElement("span");
    action.textContent = "View document";
    info.append(name, action);
    button.append(imageWrap, info);
    button.addEventListener("click", () => {
        returnFocusElement = button;
        openModal(index);
    });
    return button;
}

function buildGroups(documents) {
    const groups = new Map();
    documents.forEach((item, index) => {
        if (!groups.has(item.group)) groups.set(item.group, []);
        groups.get(item.group).push({ ...item, globalIndex: index });
    });

    for (const [letter, items] of groups) {
        const first = items[0];
        const section = document.createElement("section");
        section.className = "document-group";
        section.id = `exhibit-${letter.toLowerCase()}`;

        const heading = document.createElement("div");
        heading.className = "document-group-heading";
        const marker = document.createElement("div");
        marker.className = "document-group-letter";
        marker.textContent = letter;
        const details = document.createElement("div");
        const title = document.createElement("h3");
        title.textContent = documentTitle(first);
        details.appendChild(title);
        if (first.date) {
            const date = document.createElement("p");
            date.textContent = first.date;
            details.appendChild(date);
        }
        heading.append(marker, details);

        const grid = document.createElement("div");
        grid.className = "document-grid";
        items.forEach(item => grid.appendChild(createDocumentCard(item, item.globalIndex)));
        section.append(heading, grid);
        groupsElement.appendChild(section);
    }
}

function openModal(index) {
    if (!allDocuments.length) return;
    currentIndex = (index + allDocuments.length) % allDocuments.length;
    const item = allDocuments[currentIndex];
    modalImage.src = basePath + "web/" + item.web_filename;
    modalImage.alt = `${documentTitle(item)}: ${pageLabel(item)}`;
    modalTitle.textContent = `${documentTitle(item)}: ${pageLabel(item)}`;
    modalLink.href = basePath + "web/" + item.web_filename;
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    closeButton.focus();
}

function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    modalImage.removeAttribute("src");
    returnFocusElement?.focus();
}

closeButton.addEventListener("click", closeModal);
document.getElementById("modal-prev").addEventListener("click", () => openModal(currentIndex - 1));
document.getElementById("modal-next").addEventListener("click", () => openModal(currentIndex + 1));
modal.addEventListener("click", event => {
    if (event.target === modal) closeModal();
});
document.addEventListener("keydown", event => {
    if (!modal.classList.contains("open")) return;
    if (event.key === "Escape") closeModal();
    if (event.key === "ArrowLeft") openModal(currentIndex - 1);
    if (event.key === "ArrowRight") openModal(currentIndex + 1);
});

async function loadCollection() {
    try {
        const response = await fetch(basePath + "manifest.json");
        if (!response.ok) throw new Error(`Manifest request failed: HTTP ${response.status}`);
        const data = await response.json();
        if (!Array.isArray(data)) throw new Error("Manifest is not a list.");
        for (const item of data) {
            if (!/^[A-Z]$/.test(item.group || "") ||
                !/^[a-z0-9][a-z0-9-]*\.webp$/.test(item.web_filename || "") ||
                !/^[a-z0-9][a-z0-9-]*\.webp$/.test(item.thumbnail_filename || "")) {
                throw new Error("A manifest entry is invalid.");
            }
        }
        allDocuments = data;
        if (!data.length) {
            countElement.hidden = true;
            emptyElement.hidden = true;
            return;
        }
        countElement.textContent = `${data.length} document images in this collection`;
        emptyElement.hidden = true;
        buildGroups(data);
        if (window.location.hash.startsWith("#exhibit-")) {
            document.getElementById(window.location.hash.slice(1))?.scrollIntoView();
        }
    } catch (error) {
        console.error(error);
        countElement.textContent = "The archive could not be loaded.";
        emptyElement.textContent = "The document archive is temporarily unavailable.";
        emptyElement.hidden = false;
    }
}

loadCollection();
