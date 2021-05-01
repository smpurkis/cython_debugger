const Dockerode = require('dockerode');
const docker = new Dockerode();

class DockerManager {
    serverCmd = "python3.8 /gdb_python2_installation/cython_debugger/cygdb_server/Cygdb_server.py"
    port = "3456"
    containerName = "nodeDemo"

    constructor(hostWorkingDirectory) {
        this.hostWorkingDirectory = hostWorkingDirectory
        this.container = undefined
    }

    async createContainer() {
        this.container = await docker.createContainer({
            Image: "smpurkis/cython_debugger:latest",
            Cmd: this.serverCmd.split(" "),
            Tty: false,
            name: this.containerName,
            PortBindings: {
                "3456/tcp": [{ HostPort: this.port }]
            },
            Mounts: [
                {
                    Type: "bind",
                    Source: this.hostWorkingDirectory,
                    Target: "/project_folder"
                }
            ],
        })
    }

    async startContainer() {
        console.log(await this.container?.start());
    }

    async stopContainer() {
        console.log(await this.container?.stop());
    }

    async removeContainer() {
        console.log(await this.container?.remove());
    }
}

async function run() {
    const dockerManager = new DockerManager(
        hostWorkingDirectory="/home/sam/PycharmProjects/python/cython_debugger/demo_project"
    )
    await dockerManager.createContainer()
    await dockerManager.startContainer()
    await dockerManager.stopContainer()
    await dockerManager.removeContainer()
    // const serverCmd = "python3.8 /gdb_python2_installation/cython_debugger/cygdb_server/Cygdb_server.py"

    // const container = await docker.createContainer({
    //     Image: "docker-demo",
    //     Cmd: serverCmd.split(" "),
    //     Tty: false,
    //     name: "nodeDemo",
    //     PortBindings: {
    //         "3456/tcp": [{ HostPort: "3456" }]
    //     },
    //     Mounts: [
    //         {
    //             Type: "bind",
    //             Source: "/home/sam/PycharmProjects/python/cython_debugger/demo_project",
    //             Target: "/project_folder"
    //         }
    //     ],
    // })

    // let started = await container.start()

    // const containerRun = docker.run(
    //     image = "docker-demo",
    //     cmd = serverCmd.split(" "),
    //     outputStream = [stdout, stderr],
    //     createOptions = {
    //         Tty: false,
    //         HostConfig: {
    //             PortBindings: {
    //                 "3456/tcp": [{ HostPort: "3456" }]
    //             }
    //         }
    //     },
    // )
};
// run()