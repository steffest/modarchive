import Player from "./player.js";

document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("loaded");
    let playerElement = document.getElementById("player");

    document.addEventListener("click", (e) => {
        console.log("Document click:", e.target);
        if (e.target.classList.contains("scriptEnabled")) {
            e.preventDefault();
            e.stopPropagation();

            if (e.target.classList.contains("player")) {
                let isPopup = localStorage.getItem("player") === "popup";
                let href = e.target.getAttribute("href");
                let idMatch = href && href.match(/[?&]song_id=(\d+)/);
                let songId = idMatch ? parseInt(idMatch[1], 10) : null;

                if (!songId){
                    songId = parseInt(href.split("/").pop(), 10);
                }

                if (isPopup){
                    Player.openPopup(songId)
                }else{
                    Player.playSong(songId);
                }
            }
        }else{
            let isLink = e.target.tagName.toLowerCase() === "a" || e.target.closest("a");
            if (isLink){
                let target = e.target.tagName.toLowerCase() === "a" ? e.target : e.target.closest("a");
                let isInternal = target.target !== "_blank" && (target.hostname === window.location.hostname);
                if (isInternal &&  playerElement &&  playerElement.classList.contains("active")) {
                    e.preventDefault();
                    e.stopPropagation();
                    let href = target.getAttribute("href");
                    loadPage(href);
                }
            }
        }
    })

    // react to history changes
    window.addEventListener("popstate", (e) => {
        let url = window.location.href;
        loadPage(url,true);
    });

    if (playerElement && playerElement.classList.contains("standalone")) {
        Player.playSong();
    }
})


function loadPage(url, isPopState = false){
    fetch(url).then(res => res.text()).then(html=>{
        replaceMainContent(html);
        if (!isPopState) window.history.pushState({}, '', url);
    })
}

function replaceMainContent(html){
    // hacky but ... works
    let parser = new DOMParser();
    let doc = parser.parseFromString(html, 'text/html');
    let mainContent = doc.querySelector("main");
    let targetContent = document.querySelector("main");
    if (mainContent && targetContent){
        targetContent.innerHTML = mainContent.innerHTML;
    }
}

window.formSubmit = form=>{
    // check if whe need to handle via script
    let playerElement = document.getElementById("player");
    if (playerElement && playerElement.classList.contains("active")){
        let action = form.getAttribute("action");
        let method = (form.getAttribute("method") || "GET").toUpperCase();
        let formData = new FormData(form);
        let fetchOptions = {
            method: method,
        };
        if (method === "GET"){
            let params = new URLSearchParams(formData).toString();
            action += (action.indexOf("?") === -1 ? "?" : "&") + params;
        }else{
            fetchOptions.body = formData;
        }
        fetch(action, fetchOptions).then(res => res.text()).then(html=>{
            replaceMainContent(html);
            window.history.pushState({}, '', action);
        });
        return false;
    }
}