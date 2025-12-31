# 自定义 Entitlements 功能说明

## 功能简介
现在你可以在签名前向 IPA 文件添加自定义的 entitlements 权限。这对于需要特定权限的应用非常有用,比如推送通知、HealthKit、关联域名等。

## 使用方法

### 方式 1: 拖放文件
1. 创建一个 `.plist` 或 `.json` 文件,包含你想添加的 entitlements
2. 将该文件拖放到应用窗口中
3. 状态栏会显示 "Selected custom entitlements: [文件名]"
4. 开始签名时,这些 entitlements 会自动合并到 provisioning profile 的 entitlements 中

### 方式 2: 编程方式调用
在代码中,你可以调用:
```swift
mainView.chooseCustomEntitlementsFile()
```
这会打开文件选择对话框,让你选择一个 plist 或 json 文件。

### 方式 3: 通过菜单添加按钮(需要修改 XIB)
你可以在 Application.xib 中添加一个按钮,连接到 `chooseCustomEntitlementsFile` 方法。

## 自定义 Entitlements 文件格式

### PLIST 格式 (推荐)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>aps-environment</key>
    <string>production</string>

    <key>com.apple.developer.associated-domains</key>
    <array>
        <string>applinks:example.com</string>
    </array>
</dict>
</plist>
```

### JSON 格式
JSON 文件也支持,但需要保存为 plist 格式才能正确解析。建议使用 plist 格式。

## 示例文件
项目中包含了一个示例文件 `custom-entitlements-example.plist`,展示了常用的 entitlements 配置。

## 工作原理
1. 从 provisioning profile 中读取原有的 entitlements
2. 如果存在自定义 entitlements 文件,则读取并合并到原有 entitlements 中
3. 如果某个 key 已存在,自定义值会覆盖原有值
4. 如果 key 不存在,则添加该 entitlement
5. 最终的 entitlements 会在日志中打印出来供检查
6. 使用合并后的 entitlements 进行代码签名

## 常用 Entitlements 示例

### 推送通知
```xml
<key>aps-environment</key>
<string>production</string>
```

### 关联域名 (Universal Links)
```xml
<key>com.apple.developer.associated-domains</key>
<array>
    <string>applinks:yourdomain.com</string>
</array>
```

### 应用组 (App Groups)
```xml
<key>com.apple.security.application-groups</key>
<array>
    <string>group.com.example.myapp</string>
</array>
```

### Keychain 共享
```xml
<key>keychain-access-groups</key>
<array>
    <string>$(AppIdentifierPrefix)com.example.myapp</string>
</array>
```

### iCloud
```xml
<key>com.apple.developer.icloud-container-identifiers</key>
<array>
    <string>iCloud.com.example.myapp</string>
</array>
<key>com.apple.developer.ubiquity-kvstore-identifier</key>
<string>$(TeamIdentifierPrefix)com.example.myapp</string>
```

### HealthKit
```xml
<key>com.apple.developer.healthkit</key>
<true/>
```

### NFC
```xml
<key>com.apple.developer.nfc.readersession.formats</key>
<array>
    <string>NDEF</string>
    <string>TAG</string>
</array>
```

## 日志输出
签名过程中,日志会显示:
- 读取到的自定义 entitlements 文件
- 每个 entitlement 是新增还是覆盖
- 成功合并的 entitlements 数量
- 最终的完整 entitlements 内容

## 注意事项
1. 自定义的 entitlements 必须与你的 provisioning profile 兼容
2. 某些 entitlements 需要特定的证书或配置文件支持
3. 如果添加了不兼容的 entitlements,签名可能会失败
4. 建议在日志中检查最终的 entitlements 是否符合预期
