# RenPyUtil

<p align="center"><img src="https://www.renpy.org/static/index-logo.png"></p>

>
> 一个Ren'Py工具包，提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用。

内置文档，符合PEP257

:sparkles: 欢迎Issue, Fork和PR

## :cd: How to use 如何使用

1. 把需要要用到的[第三方库](./lib)置于你的你的游戏`game`目录下。
2. 把[RenPyUtil](./RenPyUtil)目录置于你的游戏`game`目录下即可在脚本中调用。

## :rocket: Features 功能概览

- [x] 高级角色类，轻松制作RPG和养成类游戏并拥有更多功能。
- [x] 基于socket的TCP协议多线程网络通信支持，让多个玩家在网络中通信。
- [x] ChatGPT接口适配。

......

## :bookmark: Demos 使用示范

每个模块都有对应的使用示范，请在[Demo](./Demo)中查看。

1. `advanced_character`
    - [角色任务](./Demo/demo_advanced_character/character_task.rpy)
    - [对话组](./Demo/demo_advanced_character/speaking_group.rpy)
2. `ren_communicator`
    - [客户端通信](./Demo/demo_ren_communicator/client.rpy)
    - [服务端通信](./Demo/demo_ren_communicator/server.rpy)
3. `ren_chatgpt`
    - [与ChatGPT对话](./Demo/demo_ren_chatgpt.rpy)

## :bar_chart: Module List 已经实现的所有模块

1. [`advanced_character`](./RenPyUtil/advanced_character_ren.py)
2. [`ren_communicator`](./RenPyUtil/RenCommunicator/)
3. [`ren_chatgpt`](./RenPyUtil/ren_chatgpt_ren.py)

## :book: 说明

**`resource_preserver`模块已暂时移除**

该项目使用 MIT 协议开源，但若使用需要在程序中标明。
