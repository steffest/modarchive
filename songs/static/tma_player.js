import { ChiptuneJsPlayer } from './chiptune3/chiptune3.min.js'

let isLoading = false
let songBuf = false	// for later reuse of buffer, e.g. download

init()
function init() {
	initPlayer()
}

// init ChiptunePlayer
function initPlayer() {
	window.player = new ChiptuneJsPlayer({ repeatCount: -1 })

	let song, lastPat, lastRow, lastOrder

	// listen to events
	player.onInitialized(() => {
		let params = new URLSearchParams(window.location.search)
		nextSong(params.get('song_id'))
	})
	player.onEnded((ev) => {
		if (!document.getElementById('autoplay').classList.contains('active')) {
			nextSong()
		}
	})
	player.onMetadata((meta) => {
		player.meta = meta
		document.getElementById('seekbar').max = meta.dur
		setMetadata()

		// tracker things
		song = meta.song
		lastPat = -1
		lastRow = -1
		lastOrder = -1

		renderPattern(meta.song)
		document.getElementById('orderList').innerHTML = getOrderList(meta.song);
		doResize()

		// MOD infos
		let html = ['<table>']
		if (meta.title) html.push('<tr><td>Title</td><td>', meta.title, '</td></tr>')
		if (meta.artist) html.push('<tr><td>Artist</td><td>', meta.artist, '</td></tr>')
		if (meta.date) html.push('<tr><td>Date</td><td>', meta.date, '</td></tr>')
		html.push('<tr><td>Type</td><td>', meta.type_long, '</td></tr>')
		if (meta.originaltype_long) html.push('<tr><td>Original Type</td><td>', meta.originaltype_long, '</td></tr>')
		if (meta.tracker) html.push('<tr><td>Tracker</td><td>', meta.tracker, '</td></tr>')
		if (meta.container_long) html.push('<tr><td>Container</td><td>', meta.container_long, '</td></tr>')
		if (meta.message.replace(/\n/g, '').trim().length > 0) html.push('<tr><td style="vertical-align:top">Message</td><td>', meta.message.replace(/\n/g, '<br/>'), '</td></tr>')
		if (meta.message.trim() != meta.song.samples.join('\n').trim() && meta.song.samples.join('\n').trim().length > 0) {
			html.push('<tr><td style="vertical-align:top">Samples</td><td>')
			for (let i = 0; i < meta.song.samples.length; i++) {
				if (meta.song.samples[i] != '') html.push(meta.song.samples[i], '<br/>')
			}
			html.push('</td></tr>')
		}
		html.push('</table>')

		myInfo.innerHTML = html.join('')
	})
	player.onProgress((dat) => {
		document.getElementById('seekbar').value = dat.pos

		// Return early if nothing needs to change
		if (lastOrder == dat.order && lastRow == dat.row && lastPat == dat.pattern) return

		// Order list highlighting
		if (lastOrder != dat.order) {
			// Remove highlighting from last order
			if (lastOrder != -1) document.getElementById(`order-list-${lastOrder}`).classList.remove('activeOrder')

			// Highlight the new order
			document.getElementById(`order-list-${dat.order}`).classList.add('activeOrder')
			lastOrder = dat.order
		}

		// re-render pattern if it changed
		if (lastPat != dat.pattern) {
			renderPattern(song, dat.pattern)
			lastPat = dat.pattern
			lastRow = -1
		}

		// Row highlighting
		if (lastRow != dat.row) {
			// Un-highlight the last row
			if (lastRow != -1 && document.getElementById(`pattern_${lastPat}_row_${lastRow}`) != null) {
				document.getElementById(`pattern_${lastPat}_row_${lastRow}`).classList.remove('activeOrder')
			}

			// Highlight the new row
			if (document.getElementById(`pattern_${dat.pattern}_row_${dat.row}`) != null) {
				document.getElementById(`pattern_${dat.pattern}_row_${dat.row}`).classList.add('activeOrder')
			}

			lastRow = dat.row
		}
	})
	player.onError((err) => {
		nextSong()
	})
}
function doResize() {
	// tracker.style.height = window.innerHeight - tracker.offsetTop - 10 +'px'
}
onresize = doResize
function setMetadata() {
	const metadata = player.meta
	if (!metadata) return
	document.getElementById('title').innerHTML = metadata['title']

	const subSongs = player.meta.songs
	document.getElementById('subsongs').style.display = (subSongs.length > 1) ? 'block' : 'none'
	if (subSongs.length > 1) {
		var select = document.getElementById('subsong')
		// remove old
		for (let i = select.options.length - 1; i > -1; i--) select.removeChild(select.options[i])

		for (var i = 0; i < subSongs.length; i++) {
			var elt = document.createElement('option')
			elt.textContent = subSongs[i]
			elt.value = i
			select.appendChild(elt)
		}
		select.selectedIndex = 0
		player.selectSubsong(0)
	}

	document.getElementById('seekbar').value = 0
	updateDuration()
}
function updateDuration() {
	//var sec_num = player.duration()
	var sec_num = player.meta.dur
	var minutes = Math.floor(sec_num / 60)
	var seconds = Math.floor(sec_num % 60)
	if (seconds < 10) { seconds = '0' + seconds }
	document.getElementById('duration').innerHTML = minutes + ':' + seconds
}

function renderPattern(dat, pattern) {
	const patternNum = (typeof pattern === 'undefined') ? dat.orders[0].pat : pattern

	const patternTable = document.getElementById('patternView')
	patternTable.innerHTML = ''

	const totalChannels = dat.channels.length
	const rowNumbers = dat.patterns[patternNum].rows.length

	const headerRow = document.createElement('tr')
	headerRow.id = `pattern_${patternNum}_header`

	const rowHeaderCell = document.createElement('td')
	rowHeaderCell.innerText = 'Row'
	rowHeaderCell.classList.add('row-num-col', 'fixed-col')
	headerRow.appendChild(rowHeaderCell)

	for (let i = 0; i < totalChannels; i++) {
		const headerCell = document.createElement('td')
		headerCell.classList.add('tracker-col', 'fixed-col')
		headerCell.innerText = `Ch ${i}`
		headerRow.appendChild(headerCell)
	}
	patternTable.appendChild(headerRow)

	for (let i = 0; i < rowNumbers; i++) {
		const tableRow = document.createElement('tr')
		tableRow.id = `pattern_${patternNum}_row_${i}`

		const rowCell = document.createElement('td')
		rowCell.classList.add('row-num-col', 'fixed-col')
		rowCell.innerText = i
		tableRow.appendChild(rowCell)

		for (let j = 0; j < totalChannels; j++) {
			const tableData = document.createElement('td')
			tableData.classList.add('tracker-col', 'fixed-col')
			tableData.innerText = translate(dat.patterns[patternNum].rows[i][j])
			tableRow.appendChild(tableData)
		}

		patternTable.appendChild(tableRow)
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
			if (arr[0] == 254) notePart = '^^'
			if (arr[0] == 255) notePart = '=='
		}
		ret.push(notePart)
		return ret.join('')
	}
}

function getOrderList(dat) {
	const html = []
	for (let i = 0; i < dat.orders.length; i++) {
		const cls = (i == 0) ? 'activeOrder' : ''
		let orderName = dat.orders[i].pat
		if (dat.orders[i].pat == 65534) orderName = '+++'
		if (dat.orders[i].pat == 65535) orderName = '---'

		html.push(`<div id="order-list-${i}" class="${cls}" onclick="player.setOrderRow(${i},0)">${orderName}</div>`)
	}
	return html.join('')
}

window.nextSong = (song_id) => {
	if (isLoading) return

	// TODO: Change this to retrieve the requested song
	song_id = song_id || '26849'
	let url = '/api/v1/songs/' + song_id + '/download';

	isLoading = true
	fetch(url)
		.then(r => r.arrayBuffer())
		.then(zipArrayBuffer => {
			// Use JSZip to unzip the array buffer
			return JSZip.loadAsync(zipArrayBuffer);
		})
		.then(zip => {
			// Assume there's a single audio file in the zip, you may need to adapt this based on your actual structure
			const audioFile = Object.values(zip.files)[0];

			// Set the filename in the UI
			const filename = audioFile.name.split('/').pop();
			document.getElementById('modfilename').innerText = filename;

			// Extract the audio file as an array buffer
			return audioFile.async('arraybuffer');
		})
		.then(ab => {
			songBuf = ab

			if (player.context.state != 'running') player.context.resume()
			player.play(songBuf)
			isLoading = false

			playPause.classList.remove('blink')
			sizeInKB.innerText = (songBuf.byteLength / 1024).toFixed(2)

		})
		.catch(e => console.error(e))
}
window.togglePause = () => {
	// audio policy
	if (player.context.state != 'running') {
		player.context.resume()
		return
	}
	playPause.classList.toggle('blink')
	player.togglePause()
}
window.toggleLoop = () => {
	autoplay.classList.toggle('active')
	player.setRepeatCount((autoplay.classList.contains('active')) ? -1 : 0)
}
window.toggleInfo = () => {
	btnInfo.classList.toggle('active')
	myInfo.classList.toggle('hidden')
	doResize()
}
window.saveSong = () => {
	if (!songBuf) return
	let blob = new Blob([songBuf], { type: 'application/octet-stream' })
	const a = document.createElement('a')
	a.style.display = 'none'
	a.download = modfilename.innerText
	const url = URL.createObjectURL(blob)
	a.href = url
	a.click()
	a.remove()
	blob = null
	URL.revokeObjectURL(url)
}