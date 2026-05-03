# amateurs/README.md

## 用途

这里存放素人随机抽卡的人设库。

原则：

1. 全部明确成年（`age_min >= 20`）
2. 先抽人物卡，再匹配场景
3. 人设卡必须能直接驱动 prompt
4. 少而精，优先高关联、高稳定性

## 文件说明

- `asian-japan-core.json`：第一版核心示例库
- `schema.json`：后续可补 JSON Schema 校验

## 推荐扩库顺序

1. office
2. service
3. sports
4. clinic
5. married

## 备注

- 不要只写职业名
- 不要写年龄模糊角色
- 不要写未成年联想设定
- 每条都要带 `compatible_scene_tags`
