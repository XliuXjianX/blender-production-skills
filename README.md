# Blender Production Skills

面向 Codex 的 Blender 生产级技能套件，涵盖原生建模、Geometry Nodes、模拟、绑定、材质、灯光、拓扑与场景验证，以及参考图重建工作流。

## 特点

- 以 `blender-production-router` 作为唯一制作流程与状态调度入口。
- 优先选择合适的 Blender 原生系统：Boolean、Array、Curve、Modifier、Constraint、Shader 和 Physics。
- 在字段、散布、实例、程序化拓扑或节点模拟具有明确优势时使用 Geometry Nodes。
- 支持直接拓扑、布尔开孔、楼梯阵列、曲线路径、布料、刚体、流体、水体、金属、木材与 NPR 渲染流程。
- 对本地 Blueish 资产库提供只读检索、接口检查与 Blender 5.2 运行时探测。
- 对非简单任务建立路由、构造关系、阶段、评分和技术验证 artifacts。

## 成功案例

以下是使用本套件制作或探索的部分场景与渲染案例。

<table>
  <tr>
    <td width="50%"><img src="assets/showcases/corridor-doorway.jpg" alt="走廊与门"><br><sub>走廊与门</sub></td>
    <td width="50%"><img src="assets/showcases/moonlit-bridge-viewport.jpg" alt="月下木桥 Blender 视口"><br><sub>月下木桥 Blender 视口</sub></td>
  </tr>
  <tr>
    <td><img src="assets/showcases/water-chamber.jpg" alt="水下圆形空间"><br><sub>水下圆形空间</sub></td>
    <td><img src="assets/showcases/indoor-pool.jpg" alt="室内泳池"><br><sub>室内泳池</sub></td>
  </tr>
  <tr>
    <td><img src="assets/showcases/flooded-subway-passage.jpg" alt="积水地下通道"><br><sub>积水地下通道</sub></td>
    <td><img src="assets/showcases/subway-platform.jpg" alt="地铁站台"><br><sub>地铁站台</sub></td>
  </tr>
  <tr>
    <td><img src="assets/showcases/fisheye-elevator.jpg" alt="鱼眼电梯空间"><br><sub>鱼眼电梯空间</sub></td>
    <td><img src="assets/showcases/flooded-industrial-hall.jpg" alt="积水工业空间"><br><sub>积水工业空间</sub></td>
  </tr>
  <tr>
    <td><img src="assets/showcases/station-corridor.jpg" alt="地铁通道"><br><sub>地铁通道</sub></td>
    <td><img src="assets/showcases/tiled-pool.jpg" alt="瓷砖泳池"><br><sub>瓷砖泳池</sub></td>
  </tr>
</table>

## 结构

`blender-production-router` 是顶层入口；其余目录是按领域拆分的 Specialist Skills：

- `blender-direct-surface-modeling`：点线面、BMesh、Boolean、Remesh、Sculpt 与重拓扑。
- `blender-procedural-systems`：Array、曲线、实例、散布和程序化系统。
- `blender-geometry-nodes-studio`：Geometry Nodes 图、字段、实例和模拟区。
- `blender-simulation-effects`：布料、软体、刚体、流体、水体、粒子与破碎。
- `blender-material-surfacing`：PBR 材质、金属、木材、水体与表面变化。
- `blender-geometry-validation`：拓扑、连接、碰撞、性能和场景保护检查。

## 使用

将本仓库放入 Codex 的 Skills 目录中，例如：

```text
C:\Users\Administrator\.codex\skills\blender-production-suite
```

默认目标为 Blender 5.2 LTS 与官方 Blender MCP。第三方本地资产只在已存在、可读取并通过运行时检查时作为候选，不会被自动安装或修改。

## 注意

- 本仓库不包含 Blueish 等第三方资产原文件、缓存、渲染结果或用户工程。
- 普通硬表面开孔保持原生 Boolean；普通规则楼梯保持 Array；不会为了使用节点而滥用 Geometry Nodes。
- 参考和可用性数据会随 Blender 版本与本地资产库变化而变化，应在目标环境重新探测。

## 个人主页

**CORVUS / 小红书：liu_jian**

[访问我的小红书主页](https://xhslink.cn/m/1UHWF4OwFsK)

[![CORVUS 的小红书主页](assets/corvus-xiaohongshu-profile.png)](https://xhslink.cn/m/1UHWF4OwFsK)
