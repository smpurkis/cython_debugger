<script>
    export let folderPath;
    export let folderContent;
    let showSidebar = true;
    let showButtonTexts = ["Show Folder View", "Hide Folder View"];
    let showButtonText = showButtonTexts[1];

    let filenames = [];

    function toggleSidebar() {
        showSidebar = !showSidebar;
        showButtonText = showButtonTexts[showButtonTexts.length-1 - showButtonTexts.indexOf(showButtonText)]
        if (showSidebar) {
            filenames = [...folderContent]
        } else {
            filenames = filenames.fill("")
        }
    }
</script>

<div class="FolderView">
    <h4>{folderPath}</h4>
    <button on:click={toggleSidebar} class="showButton">
        <h5>{showButtonText}</h5>
    </button>
    <div class="contentBox">
        {#each filenames as id, i}
        <button
            on:click={toggleSidebar}
            class:hideSidebar={!showSidebar}
            class:showSidebar>
            {id}
        </button>
        {/each}
    </div>
</div>


<style>
    @import "https://unpkg.com/chota@latest";

    .FolderView {
		display: flex;
        align-items: flex-start;
        flex-direction: column;
        width: 200px;
		left: 20px;
		top: 20px;
	}

    .showButton {
        align-items: flex-start;
        margin-bottom: 5px;
        border-radius: 10px;
    }

    .contentBox {
        display: flex;
        flex-direction: column;
        background-color: rgb(37, 35, 35);
    }

    h4 {
        color: white;
    }

    .showSidebar {
        color: white;
        background-color: rgb(37, 35, 35);
        outline: blueviolet;
        height: auto;
        font-size: 0.9em;
        text-align: left;
        overflow-x: auto;
        transition: height 0.1s;
        transition-timing-function: ease-out;

    }

    .hideSidebar {
        display: none;
        color: white;
        background-color: rgb(37, 35, 35);
        background:transparent;
        display: relative;
        height: 0px;
        width: 0px;
        overflow-x: hidden;
        transition: height 0.1s;
        transition-timing-function: ease-in;
    }
</style>
