# RenPyUtil

<p align="center">
  <img src="https://www.renpy.org/static/index-logo.png" alt="Ren'Py logo">
</p>

> 一个 Ren'Py 工具包，提供了一系列基于Ren'Py的功能类，供Ren'Py开发者调用。

## :cd: 如何使用

> 为了更好地开发和兼容非 Ren'Py 环境，未来所有的模块都将转换为可导入的Python库，目前暂时保留 `_ren.py` 形式

- 将 [RenPyUtil](./RenPyUtil) 目录放置于您的游戏 `game` 目录下。~~*（预计废除）*~~
- 将 [python-packages](./python-packages/) 目录放置于您的游戏 `game` 目录下。

## :rocket: 功能概览

- [x] 轻松创建RPG和养成类游戏，具备丰富功能。
- [x] ~~基于socket的TCP协议多线程网络通信模块，让多个玩家可以在网络中交流。~~*(已废弃)*
- [x] 轻量化异步 websocket 通信框架，用于在 Ren'Py 游戏中实现网络通信。兼容 Ren'Py 和非 Ren'Py 环境。适用于小型网络游戏。*(测试)*
- [x] ~~ChatGPT 接口适配，便于集成智能对话功能。~~ *(已过时)*
- [x] Positioner 定位工具，更加便捷地定位游戏内的组件位置。
- [x] 对 `Live2D` 提供更高级的支持。*(存在问题)*

---

## :bookmark: 使用示范

每个模块都有相应的使用示范（迁移至`python-packages`目录中的模块的demo可能已经过时），请在 [Demo](./Demo) 中查看。

1. **`advanced_character`**
    - [角色任务示例](./Demo/demo_advanced_character/character_task.rpy)
    - [对话组示例](./Demo/demo_advanced_character/speaking_group.rpy)
2. **`ren_communicator`**
    - [客户端通信示例](./Demo/demo_ren_communicator/client.rpy)
    - [服务端通信示例](./Demo/demo_ren_communicator/server.rpy)
3. **`ren_chatgpt`**
    - [与ChatGPT对话示例](./Demo/demo_ren_chatgpt.rpy)
4. **`InteractiveLive2D`**
    - [Live2D示例](./Demo/demo_InteractiveLive2D.rpy)

## :bar_chart: 已实现模块列表

1. [`advanced_character`](./RenPyUtil/advanced_character_ren.py)
2. [`ren_communicator`](./RenPyUtil/RenCommunicator/)
3. [`ren_chatgpt`](./RenPyUtil/ren_chatgpt_ren.py)
4. [`InteractiveLive2D`](./RenPyUtil/00InteractiveLive2D_ren.py/)

## :bulb: 工具
1. [`Positioner`](./RenPyUtil/Positioner)

## :book: 说明

**`resource_preserver`模块已暂时移除。**

**`python-packages`目录下均为依赖的第三方库或重写的模块，以后大部分模块都将迁移至其中，请优先考虑使用。**

**该项目使用MIT协议开源，使用时请在程序中注明。**
