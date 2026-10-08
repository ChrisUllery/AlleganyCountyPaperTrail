const MANIFEST_URL =
    "../assets/documents/luke-mill/manifest.json";

const WEB_BASE =
    "../assets/documents/luke-mill/web/";

const THUMB_BASE =
    "../assets/documents/luke-mill/thumbs/";


const GROUP_INFO = {

    A: {
        title: "Memorandum of Understanding with Port River West",
        date: "August 7, 2024"
    },

    B: {
        title: "Property Purchase Example",
        date: ""
    },

    C: {
        title: "Deed: West Virginia Property",
        date: ""
    },

    D: {
        title: "Board of County Commissioners Public Meeting Agenda",
        date: "July 10, 2025"
    },

    E: {
        title: "Closed Session Notice",
        date: ""
    },

    F: {
        title: "Board of County Commissioners Public Meeting Agenda",
        date: "August 8, 2024"
    },

    G: {
        title: "Board of County Commissioners Public Meeting Agenda",
        date: "August 22, 2024"
    },

    H: {
        title: "Agreement with Port River West",
        date: "July 10, 2025"
    },

    I: {
        title: "Board of County Commissioners Public Meeting Agenda",
        date: "July 10, 2025"
    },

    J: {
        title: "BOCC Agenda Packet: Signed Documents",
        date: "July 10, 2025"
    },

    K: {
        title: "Off the Grid Energy Works Email: Proposed Data Center",
        date: "July 17, 2025"
    }

};


let allDocuments = [];
let currentIndex = 0;


function getPageLabel(item) {

    if (item.page) {
        return `Page ${item.page}`;
    }

    return "Document";
}


function createDocumentCard(item, index) {

    const button = document.createElement("button");

    button.className = "document-card";
    button.type = "button";

    const thumbnail =
        THUMB_BASE + item.thumbnail_filename;

    button.innerHTML = `
        <div class="document-thumb-wrap">

            <img
                src="${thumbnail}"
                alt="${getPageLabel(item)}"
                loading="lazy"
            >

        </div>

        <div class="document-card-info">

            <strong>
                ${getPageLabel(item)}
            </strong>

            <span>
                View document
            </span>

        </div>
    `;

    button.addEventListener(
        "click",
        () => openModal(index)
    );

    return button;
}


function buildGroups(manifest) {

    const container =
        document.getElementById("document-groups");

    const grouped = {};

    manifest.forEach((item, index) => {

        if (!grouped[item.group]) {
            grouped[item.group] = [];
        }

        grouped[item.group].push({
            ...item,
            globalIndex: index
        });
    });


    Object.keys(grouped).forEach(group => {

        const info = GROUP_INFO[group];

        const section =
            document.createElement("section");

        section.className = "document-group";

        section.id = `exhibit-${group.toLowerCase()}`;


        const heading =
            document.createElement("div");

        heading.className = "document-group-heading";


        const dateText =
            info?.date
                ? `<p>${info.date}</p>`
                : "";


        heading.innerHTML = `
            <div class="document-group-letter">
                ${group}
            </div>

            <div>
                <h3>
                    ${info?.title || "Document"}
                </h3>

                ${dateText}
            </div>
        `;


        const grid =
            document.createElement("div");

        grid.className = "document-grid";


        grouped[group].forEach(item => {

            grid.appendChild(
                createDocumentCard(
                    item,
                    item.globalIndex
                )
            );

        });


        section.appendChild(heading);
        section.appendChild(grid);

        container.appendChild(section);

    });

}


function openModal(index) {

    currentIndex = index;

    const item =
        allDocuments[currentIndex];

    const modal =
        document.getElementById("document-modal");

    const image =
        document.getElementById("modal-image");

    const title =
        document.getElementById("modal-title");

    const link =
        document.getElementById("modal-full-link");


    const info =
        GROUP_INFO[item.group];


    image.src =
        WEB_BASE + item.web_filename;

    image.alt =
        `${info?.title || "Document"}: ${getPageLabel(item)}`;


    title.textContent =
        `${info?.title || "Document"}: ${getPageLabel(item)}`;


    link.href =
        WEB_BASE + item.web_filename;


    modal.classList.add("open");

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.classList.add(
        "modal-open"
    );

}


function closeModal() {

    const modal =
        document.getElementById("document-modal");

    const image =
        document.getElementById("modal-image");


    modal.classList.remove("open");

    modal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.classList.remove(
        "modal-open"
    );


    setTimeout(() => {

        if (!modal.classList.contains("open")) {
            image.src = "";
        }

    }, 200);

}


function previousDocument() {

    currentIndex--;

    if (currentIndex < 0) {
        currentIndex =
            allDocuments.length - 1;
    }

    openModal(currentIndex);
}


function nextDocument() {

    currentIndex++;

    if (currentIndex >= allDocuments.length) {
        currentIndex = 0;
    }

    openModal(currentIndex);
}


async function loadDocuments() {

    try {

        const response =
            await fetch(MANIFEST_URL);


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        allDocuments =
            await response.json();


        document.getElementById(
            "document-count"
        ).textContent =
            `${allDocuments.length} document images in this collection`;


        buildGroups(allDocuments);

    }

    catch (error) {

        console.error(error);

        document.getElementById(
            "document-count"
        ).textContent =
            "The document archive could not be loaded.";

    }

}


document.getElementById(
    "modal-close"
).addEventListener(
    "click",
    closeModal
);


document.getElementById(
    "modal-prev"
).addEventListener(
    "click",
    previousDocument
);


document.getElementById(
    "modal-next"
).addEventListener(
    "click",
    nextDocument
);


document.getElementById(
    "document-modal"
).addEventListener(
    "click",
    event => {

        if (
            event.target.id ===
            "document-modal"
        ) {
            closeModal();
        }

    }
);


document.addEventListener(
    "keydown",
    event => {

        const modal =
            document.getElementById(
                "document-modal"
            );

        if (
            !modal.classList.contains("open")
        ) {
            return;
        }


        if (event.key === "Escape") {
            closeModal();
        }

        if (event.key === "ArrowLeft") {
            previousDocument();
        }

        if (event.key === "ArrowRight") {
            nextDocument();
        }

    }
);


loadDocuments();
