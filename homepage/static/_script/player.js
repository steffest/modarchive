import { ChiptuneJsPlayer } from './chiptune3/chiptune3.js'
import Range from './range.js'

let Player = (()=>{
    let me = {};

    let isLoading = false;
    let songBuf = false;
    let container;
    let player;
    let currentId;
    let UI = {
        patternTop: 53
    };
    let songInfo = {
        playback: "stereo",
    };

    // dummy playlist
    let playList = []

    me.init = function(id){
        console.log("Player.init()");

        if (player) {
            console.log("Player already initialized");
        }

        const context = new AudioContext();

        container = document.getElementById("player");
        player = new ChiptuneJsPlayer(
            {
                repeatCount: -1,
                stereoSeparation:100,
                context: context
            })
        window.player = player; // for debug

        const merger = context.createChannelMerger(1);

        player.gain.connect(context.destination);

        player.onInitialized(() => {
            let params = new URLSearchParams(window.location.search);
            me.playSong(id || params.get('song_id'));
        })
        player.onEnded((ev) => {
            console.log("player.onEnded()", ev)
        })
        player.onMetadata((meta) => {
            if (UI.progressBar){
                UI.progressBar.setMax(meta.dur);
            }
            songInfo.meta = meta;
            songInfo.lastPattern = -1;
            songInfo.lastRow = -1

            updateMetaInfo();
            renderPattern();
        })
        player.onProgress((data) => {
            if (data.pos && UI.progressBar && !UI.progressBar.hasInput()) {
                UI.progressBar.setValue(data.pos);
            }

            if (songInfo.lastPattern !== data.pattern) {
                renderPattern(data.pattern)
                songInfo.lastPattern = data.pattern
                songInfo.lastRow = -1
            }

            if (songInfo.lastRow !== data.row) {
                UI.patternView.style.top = ((-data.row * 16) + UI.patternTop) + "px"
                songInfo.lastRow = data.row;
            }
        })
        player.onError((err) => {
            console.error(data)
        })

        UI.panelLeft = createPanel();
        UI.panelRight = createPanel();

        let volumePanel = document.createElement("div");
        volumePanel.id = "volumePanel";
        UI.panelLeft.appendChild(volumePanel);

        let volumeButton = document.createElement("button");
        volumeButton.classList.add("volume");
        volumePanel.appendChild(volumeButton);
        volumeButton.onclick = () => {
            console.error(UI.volumeSlider.getValue());
            if (UI.volumeSlider.getValue()){
                UI.volumeSlider.prevValue = UI.volumeSlider.getValue();
                UI.volumeSlider.setValue(0);
                UI.volumeSlider.onInput();
            }else{
                console.error("reset",UI.volumeSlider.prevValue);
                UI.volumeSlider.setValue(UI.volumeSlider.prevValue || 100);
                UI.volumeSlider.onInput();
            }
        }

        UI.volumeSlider = Range({
            onInput: () => {
                let volume = parseInt(UI.volumeSlider.getValue()) / 100;
                player.gain.gain.setValueAtTime(volume, context.currentTime);
                if (volume > 0){
                    volumeButton.classList.remove("muted");
                }else{
                    volumeButton.classList.add("muted");
                }
            },
            value:100
        });
        volumePanel.appendChild(UI.volumeSlider.elm);


        UI.maindisplay = document.createElement("div");
        UI.maindisplay.id = "mainDisplay";
        UI.panelLeft.appendChild(UI.maindisplay);

        UI.titleDisplay = document.createElement("h1");
        UI.maindisplay.appendChild(UI.titleDisplay);
        UI.infoLeft = document.createElement("div");
        UI.infoLeft.className = "left"
        UI.maindisplay.appendChild(UI.infoLeft);
        UI.infoRight = document.createElement("div");
        UI.infoRight.className = "right"
        UI.maindisplay.appendChild(UI.infoRight);

        UI.progressBar = Range({
            onChange: ()=>{
                player.setPos(UI.progressBar.getValue());
            }
        });

        UI.panelLeft.appendChild(UI.progressBar.elm);

        UI.buttons = document.createElement("div");
        UI.buttons.id = "playerButtons";
        UI.panelLeft.appendChild(UI.buttons);


        createButton("Mono", "Switch to Mono", button=>{
            player.gain.disconnect();
            console.error(button.innerText);
            if (button.innerText === "Stereo") {
                merger.disconnect();
                player.gain.connect(context.destination);
                button.innerText = "Mono";
                songInfo.playback = "stereo";
                button.classList.remove("active");
                button.title = "Switch to Mono";
            }else{
                player.gain.connect(merger);
                merger.connect(context.destination);
                button.innerText = "Stereo";
                songInfo.playback = "mono";
                button.classList.add("active");
                button.title = "Switch to Stereo";
            }
            updateMetaInfo();
        });

        createButton("Prev", "Play Previous Song" , button=>{
            gotoPlaylist(-1);
        })


        UI.playButton = createButton("Pause", "Pause playback" ,button=>{
            if (context.state !== 'running') context.resume()
            if (button.innerText === "Pause") {
                player.pause();
                button.innerText = "Play";
                button.classList.add("active")
            }else{
                player.unpause();
                button.innerText = "Pause";
                button.classList.remove("active")
            }
        })

        createButton("next", "Play Next Song",button=>{
            gotoPlaylist(1);
        })


        let bLabel = window.opener ? "Pop In" : "Pop Out";
        createButton(bLabel, bLabel + " player",button=>{
            player.pause();
            if (container.classList.contains('standalone')) {
                if (window.opener && window.opener.popIn){
                    window.opener.popIn();
                }else{
                    // we lost the context of the main window: just close the popup;
                    localStorage.removeItem("player");
                    window.close();
                }
            }else{
                me.openPopup(currentId);
            }
        })

        UI.infoButton = document.createElement("button");
        UI.infoButton.className = "info";
        UI.infoButton.title = "Show/Hide info";
        UI.infoButton.onclick = ()=>{
            console.error(UI.infoLeft);
            UI.infoLeft.classList.toggle("hidden");
            UI.infoRight.classList.toggle("hidden");
        }
        UI.panelLeft.appendChild(UI.infoButton);


        let visualizer = document.createElement("div");
        visualizer.id = "visualizer";
        UI.panelRight.appendChild(visualizer);

        UI.patternView = document.createElement("div");
        UI.patternView.id = "patternView";
        visualizer.appendChild(UI.patternView);

        UI.topBar = document.createElement("div");
        UI.topBar.id = "topBar";
        visualizer.appendChild(UI.topBar);

        UI.centerBar = document.createElement("div");
        UI.centerBar.id = "centerBar";
        visualizer.appendChild(UI.centerBar);

        UI.bottomBar = document.createElement("div");
        UI.bottomBar.id = "bottomBar";
        visualizer.appendChild(UI.bottomBar);


        container.classList.add("active");
    }

    me.playSong = (id)=>{
        console.log("Play song",id);

        if (!player){
            me.init(id);
            return;
        }

        if (isLoading) return;
        currentId = id;

        let url = '/api/v1/download/' + id;
        isLoading = true;

        fetch(url)
            .then(r => r.arrayBuffer())
            .then(zipArrayBuffer => {
                // Use JSZip to unzip the array buffer
                return JSZip.loadAsync(zipArrayBuffer);
            })
            .then(zip => {
                // Assume there's a single audio file in the zip, you may need to adapt this based on your actual structure
                const audioFile = Object.values(zip.files)[0];


                const filename = audioFile.name.split('/').pop();
                UI.titleDisplay.innerHTML = filename;
                songInfo.title = filename;
                //songInfo.artist = data.artistName;

                // Extract the audio file as an array buffer
                return audioFile.async('arraybuffer');
            })
            .then(ab => {
                songBuf = ab

                if (player.context.state !== 'running') player.context.resume()
                player.play(songBuf)
                isLoading = false
                if (container) container.classList.add("active");
                if (UI.playButton){
                    UI.playButton.classList.remove("active");
                    UI.playButton.innerText = "Pause";
                }

                setTimeout(()=>{
                    if (player.context.state !== 'running'){
                        UI.playButton.classList.add("active");
                        UI.playButton.innerText = "Play";
                    }
                },100);

                songInfo.fileSize = (songBuf.byteLength / 1024).toFixed(2);
                updateMetaInfo();

                //sizeInKB.innerText = (songBuf.byteLength / 1024).toFixed(2)

            })
            .catch(e => console.error(e))

    }

    me.openPopup = function(id){
        let url = "/songs/player/?song_id=" + id;
        let popup = window.open(url, "ModPlayer", "width=500,height=400");
        popup.document.title = "Mod Player";
        localStorage.setItem("player", "popup");
        if (container) container.classList.remove("active");

        window.popIn = function(){
            if (popup && popup.close) popup.close();
            localStorage.removeItem("player");
            me.playSong(id);
        }
    }

    function updateMetaInfo(){
        let meta = songInfo.meta || {};
        if (UI.infoRight){
            let info = [];
            if (meta.type_long) info.push(meta.type_long);
            if (meta.song){
                if (meta.song.channels) info.push(meta.song.channels.length + " channels");
                if (meta.song.patterns) info.push(meta.song.patterns.length + " patterns");
            }
            UI.infoRight.innerHTML = info.join("<br>");
        }

        if (UI.infoLeft){
            let info = [];
            info.push("Artist: " + (meta.artist || songInfo.artist));
            info.push("Size: " + songInfo.fileSize + " KB");
            info.push("Playback: " +  songInfo.playback);
            UI.infoLeft.innerHTML = info.join("<br>");
        }
    }

    function gotoPlaylist(offset){
        let index = playList.indexOf(currentId) || 0;
        index = (index + offset + playList.length) % playList.length;
        let id = playList[index];
        me.playSong(id);
    }

    function createButton(label, info, onClick){
        let button = document.createElement("button");
        button.innerText = label;
        button.className = label.toLowerCase().replace(" ", "");
        button.title = info;
        button.onclick = ()=>onClick(button);
        UI.buttons.appendChild(button);
        return button;
    }

    function createPanel() {
        let panel = document.createElement("div");
        panel.classList.add("panel");
        container.appendChild(panel);
        return panel;
    }

    function renderPattern(index) {
        let song = songInfo.meta.song;

        const patternNum = (typeof index === 'undefined') ? song.orders[0].pat : index
        UI.patternView.innerHTML = ''

        const totalChannels = song.channels.length
        const rowNumbers = song.patterns[patternNum].rows.length


        for (let i = 0; i < rowNumbers; i++) {
            const row = document.createElement('div')
            row.className = "prow";

            let data = [];
            data.push(b(i.toString().padStart(2, '0')));
            for (let j = 0; j < totalChannels; j++) {
                data.push(translate(song.patterns[patternNum].rows[i][j]))
            }

            row.innerHTML = data.join(" ");

            UI.patternView.appendChild(row)
        }

        function translate(arr) {
            let ret = []

            const effects = '-0123456789ABCDEFFHEJKLMNOPQRSTUVWXYZ'
            let notePart = '---'
            let instrumentPart = '--'
            if (arr[0] !== 0) {
                const notesPerOct = 'C|C#|D|D#|E|F|F#|G|G#|A|A#|B'.split('|')
                const oct = Math.floor((arr[0] - 1) / 12.0)	// notesPerOct.length
                notePart = notesPerOct[(arr[0] - 1) % 12]
                notePart = notePart.padEnd(2, '-')
                notePart += oct

                instrumentPart = arr[1].toString().padStart(2, '0')
                if (arr[0] == 254) notePart = '^^^'
                if (arr[0] == 255) notePart = '==='
            }
            ret.push(notePart)
            ret.push(em(instrumentPart))
            return ret.join('')
        }

        function b(s){
            return '<b>' + s + '</b>';
        }

        function em(s){
            return '<em>' + s + '</em>';
        }
    }


    return me;
})()

export default Player