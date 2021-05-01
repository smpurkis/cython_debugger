<script>
	const { ipcRenderer } = require("electron");

	import { Input, Button } from "svelte-chota";

	import TextDisplay from "./TextDisplay.svelte";
	import FolderView from "./FolderView.svelte";

	// import { DockerManager } from "./DockerManager.js";
	export let name;
	let count = 1;
	let openFileContent = "";
	let openFolderContent = [1,2,3];
	let folderPath = "Please Select Folder";
	let inputSize;

	function onClick() {
		count = count + 2;
		console.log("hello");
	}

	ipcRenderer.on("file-opened", (event, file, content) => {
		openFileContent = content;
		inputSize = content.split(/\r?\n/).length;
	});

	ipcRenderer.on("folder-opened", (event, folder, folderContent) => {
		openFolderContent = folderContent;
		folderPath = folder;
	});

	ipcRenderer.on("save-file", (event, file, content) => {
		openFileContent = content;
		inputSize = content.split(/\r?\n/).length;
		console.log(inputSize);
	});
</script>

<main>
	<h1>Hello {name}!</h1>
	<p>
		Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn
		how to build Svelte apps.
	</p>
	<Button primary on:click={onClick}>
		Hello world, counter {count}
	</Button>
	<Button primary on:click={onClick}>
		Hello world, counter {count}
	</Button>
	<p />

	<div class="body">
		<FolderView folderPath={folderPath} folderContent={openFolderContent} />
		<TextDisplay {openFileContent} {inputSize} />
	</div>
</main>

<style>
	@import "https://unpkg.com/chota@latest";

	.body {
		display: flex;

	}

	p {
		color: white;
	}

	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
		background-color: rgb(37, 35, 35);
	}

	h1 {
		color: #ff3e00;
		/* text-transform: uppercase;
		font-size: 4em;
		font-weight: 100; */
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>
