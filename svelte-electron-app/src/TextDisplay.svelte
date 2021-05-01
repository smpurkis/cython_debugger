<script>
    export let openFileContent;
    export let inputSize = 10;
    
    function autoGrow() {
        openFileContent = openFileContent;
        inputSize = Math.max(openFileContent.split(/\r?\n/).length + 2, 10);
    }
</script>

<p>
    <textarea
        type="text"
        placeholder="Please open a file..."
        bind:value={openFileContent}
        rows={inputSize}
        class="textarea"
        on:input={autoGrow}
    />
</p>



<style>
    @import "https://unpkg.com/chota@latest";

    .textarea {
        background-color: rgb(73, 72, 72);
        width: 100em;
        margin-top: 50px;
        color: rgba(223, 223, 223, 0.89);
    }
</style>
