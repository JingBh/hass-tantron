# hass-tantron

Custom Home Assistant integration for Tantron devices / 小泰助手设备接入 Home Assistant

## Installation

This project is still a work in progress. In the meantime, you can manually clone the repo and install it as a custom component if you want to try it out. When the project is more stable, it will be published to somewhere like HACS. 

仍在开发中，敬请期待。

## Features

目前已实现的功能：
- 登录小泰助手账号
- 获取家庭列表
- 获取家庭所在位置天气
- 获取网关在线状态
- 获取家庭房间列表
- 获取家庭设备列表

开发中的功能：
- 获取设备状态
- 控制设备

## Known Issues

This integration is tested against my own devices only, does not guarantee to support all features of all devices. If you find your device not working properly, please open an issue with the diagnostics output of your config entry or device entry in Home Assistant.

此集成目前仅在我自己的设备上测试过，不保证支持所有设备。如果你发现你的设备无法正常工作，请在 HomeAssistant 上获取集成或设备的诊断输出，然后开一个 issue。

Pull requests that adds or completes support for more devices are always welcome.

欢迎提出添加更多设备支持的 Pull Request。

## Disclaimer

This is a third-party integration. The developer is not affiliated with Tantron Group or Home Assistant in any way. The integration is open-source, and is intended for personal use only, do not use it for commercial purposes.

这是一个第三方集成，开发者与泰创科技或 Home Assistant 没有任何关联。本集成是开源项目，仅供个人使用，不得用于商业用途。小泰助手是泰创科技旗下的智能家居应用，本项目所引用的相关名称、商标等知识产权归其原本所有者所有。
