# Divoom-Timebox (Warning: Currently in Alpha-state)

This is a [Home Assistant](https://hass.io) custom component for the Timebox-Evo. 
Currently, the only way to interact with the Timebox-Evo is a Javascript library ([node-divoom-timebox-evo](https://github.com/RomRider/node-divoom-timebox-evo)).
I am working on implementing it in this Repository. This Repository is still in an alpha-state, as i add new features.

# Installation

## Finding mac address of your Timebox-Evo

First, you will have to find the mac address of your Timebox-Evo. 
There are multiple methods to find your bluetooth mac address. 
You can:
1. Use a phone app
>[IOS](https://apps.apple.com/us/app/bluetooth-ble-device-finder/id1465245157)

>[Android](https://play.google.com/store/apps/details?id=com.codeweavers.bluetoothmacaddressfinder)

2. Use Home Assistant
> run `bluetoothctl`

> run `scan on`

A list of blutooth devices will appear. Write down the mac address of your Timebox-Evo

You can try to connect to it to ensure it will work
- run `connect MAC_ADDRESS`
  > If you have the error `Failed to connect: org.bluez.Error.Failed` run `trust MAC_ADDRESS` and try again
- if it worked, disconnect the device, run `disconnect`

If you have any problem, [the following guide](https://www.pcsuggest.com/linux-bluetooth-setup-hcitool-bluez/) may help you troubleshoot your issue.

## Server

The javascript server will communicate with the Timebox-Evo.
You will have to set this up on your network.
The default server port is 5555, it is possible to override using the `PORT` environment variable

## Server options
> Run using [Portainer](https://github.com/alexbelgium/hassio-addons/tree/master/portainer)
Todo: portainer instructions
> Run on an external network-device.

### Requirement

The server must have bluetooth to communicate with the Timebox-Evo.
It is possible to use an external or the internal bluetooth adapter.

### Installation with docker

Docker is the recommended way of installing the server, as it is easy to use.

docker
```sh
docker run --network host anonymoesje/divoom-timebox
```

docker-compose.yml
```yml
version: '3'

services:
  timebox-server:
    container_name: timebox-server
    image: anonymoesje/divoom-timebox
    network_mode: host
    restart: unless-stopped
```

### npm Installation

- clone the repository
- go in the `./server` folder
- run `npm install`. Any dependencies issues are most likely caused because of a lack of bluetooth dependencies
- run `npm build`

Then `npm run-script start` to start the server

## HACS custom component

### Install the component in the HACS market

#### Enable the component

Setup through the integrations UI, following values are needed to enable the light and notify platforms:
- `name`: name of light entity
- `mac`: mac address of your timebox-evo
- `url`: url to the server
- `image_dir` (optional): a directory, relative to the configuration dir.

# Functionality

Currently is is possible to:
- Display an image from an url
- Display an local image
- Change the brightness using the light entity
- Display scrolling text
- Switching to the time-display

# Usage

This custom component acts as both light and notify platform. 
The Notify platform can send all messages to the server. 
I will continue changing the messages to entities. 

Currently it is possible to use all actions through the Notify Service.
You can also specify TimeBox mode and other information in the fields parameter of the Service Data payload.

## Display an image

### From a link
```
service: timebox.send
data:
  fields:
    mode: image
    text: "https://example.com/picture.png"
```

### From a local file
```
service: timebox.send
data:
  fields:
    mode: "image",
    file-name: "picture.png"
```
In order to use a local file you must specify an `image_dir` in the config
The service will use the image in: `image_dir/FILENAME`

## Change the brightness
```
service: timebox.send
data:
  fields:
    mode: "brightness",
    brightness: 100
```
It is possible to change the brightness on a scale of 0 to 100
This is the same functionality as the light-entity

## Display text
```
service: timebox.send
data:
  fields:
    mode: "text",
    text: "Hello, World!"
```

## Switch to the time panel
```
service: timebox.send
data:
  fields:
    mode: "time"
    display-type": "analog-round"
```
Display-type options: 
>`fullscreen` (default & empty)
>`fullscreen-negative`
>`with-box`
>`rainbow`
>`analog-round`
>`analog-square`

## Updating timebox utc offset
```
service: timebox.send
data:
  fields:
    mode: "time",
    set-datetime: true
    datetime-offset: "-03:00"
```
If `datetime-offset` is not specified, the local time home-assistant is used.

# Examples
TODO

# Credit

Thanks to 
> [node-divoom-timebox-evo](https://github.com/RomRider/node-divoom-timebox-evo).

> [homeassistant-timebox](https://bitbucket.org/pjhardy/homeassistant-timebox/src/master/).

> [timebox-home-assistant](https://github.com/noeRls/timebox-home-assistant)