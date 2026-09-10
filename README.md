# Tennis Collection Robot 2.0

现代化的网球收集机器人视觉与路径规划项目。原始工程基于 2017 年的 C++、OpenCV 3.x、OpenCV SVM 和 Linux 预编译库；本版本以纯 Python 重新实现主流程，适合作为计算机视觉、机器人算法和工程化岗位项目展示。

## 能力升级

- **现代视觉链路**：HSV + 形态学作为低延迟 CPU 基线，可选 Ultralytics YOLO 作为数据驱动检测后端。
- **在线跟踪**：质心匹配、速度预测、EMA 平滑、遮挡短时保持，避免逐帧抖动和重复计数。
- **路径规划**：小规模目标使用 Held-Karp 精确解，大规模目标使用最近邻 + 2-opt，自动合并可一次收集的近邻球。
- **坐标标定**：支持 YAML 单应性矩阵，将像素坐标映射到场地/机器人坐标；默认保留像素坐标模式便于开箱演示。
- **工程化交付**：PySide6 控制台、无界面 CLI、配置文件、类型标注、单元测试、可选 AI 依赖和 GitHub Actions。

## 快速运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest

# 用仓库样例图片进行无界面检测，输出到 outputs/annotated.jpg
tennis-robot --config config/default.yaml --headless

# 启动 PySide6 控制台
tennis-robot-ui
```

相机运行可在 `config/default.yaml` 中将 `source` 改为 `0`、`1` 等设备编号。视频文件会逐帧处理；图片模式处理一帧后结束。

## YOLO 模式

```powershell
python -m pip install -e ".[ai]"
```

然后将配置改为：

```yaml
detector:
  backend: yolo
  model_path: models/tennis-ball.pt
  confidence: 0.45
```

建议使用自采集的不同光照、背景、遮挡和球体距离数据训练/验证模型，并记录 precision、recall、mAP50-95、端到端延迟和漏检后的安全策略。HSV 后端用于快速基线和无模型演示，YOLO 后端用于生产级复杂场景升级。

## 面向岗位的展示点

1. 视觉算法：颜色空间、形态学、轮廓几何、检测器接口和单应性标定。
2. 机器人算法：在线跟踪、TSP/VRP 思路、精确算法与启发式算法的复杂度取舍。
3. 工程能力：配置驱动、可测试模块、CLI/GUI 双入口、可选依赖、性能指标和可复现实验。
4. 可扩展方向：ROS 2 节点、Nav2/底盘适配、深度相机 3D 定位、ONNX/TensorRT 部署、Prometheus 指标与远程运维。

## 目录

```text
src/tennis_robot/
  vision.py       # HSV/YOLO 检测后端
  tracking.py     # 在线目标跟踪
  planner.py      # 精确与启发式路径规划
  pipeline.py     # 检测-跟踪-规划主链路
  ui.py           # PySide6 操作台
  cli.py          # 无界面入口
config/           # 可复用运行配置
tests/            # 算法和视觉回归测试
data/             # 小型演示数据
```

## 迁移说明

旧版 C++ 源码、`.so`、预编译可执行文件和 OpenCV XML SVM 模型未复制到 Python 包中，因为它们与当前运行时和部署平台绑定。原始压缩包仍保留在用户提供的位置，可作为算法历史参考；Python 版本的主链路不依赖 C++ 编译器或 Linux 动态库。

## 安全与许可

连接真实底盘前必须加入急停、限速、目标丢失和通信超时保护，并在仿真或架空测试中验证。模型权重、数据集和原始论文/代码的许可应在公开发布前单独核查。

