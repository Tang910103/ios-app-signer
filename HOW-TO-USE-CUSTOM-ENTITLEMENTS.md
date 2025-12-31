# 如何使用自定义 Entitlements 功能

## 三种使用方法

### 方法 1: 通过菜单选择(推荐) ⭐️

1. 在应用菜单栏,点击 **View** -> **Choose Custom Entitlements...**
2. 在打开的文件选择对话框中,选择你的 `.plist` 文件
3. 状态栏会显示 "Selected custom entitlements: xxx.plist"
4. 正常进行签名操作

### 方法 2: 拖放文件

1. 准备好你的自定义 entitlements plist 文件
2. 直接将该文件**拖放到应用窗口中**
3. 状态栏会显示 "Selected custom entitlements: xxx.plist"
4. 正常进行签名操作

### 方法 3: 在每次签名前拖放

你也可以在每次签名前,先拖放 IPA 文件,再拖放 entitlements plist 文件,然后点击 Start 按钮。

## 快速开始示例

### 步骤 1: 创建自定义 entitlements 文件

创建一个名为 `my-entitlements.plist` 的文件:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- 启用推送通知 -->
    <key>aps-environment</key>
    <string>production</string>

    <!-- 启用 Universal Links -->
    <key>com.apple.developer.associated-domains</key>
    <array>
        <string>applinks:yourdomain.com</string>
    </array>
</dict>
</plist>
```

### 步骤 2: 在应用中选择该文件

- 点击菜单: **View** -> **Choose Custom Entitlements...**
- 或者直接拖放该文件到应用窗口

### 步骤 3: 正常签名

选择你的 IPA 文件、证书、Provisioning Profile,然后点击 Start。

### 步骤 4: 验证结果

在签名过程中,打开 **View** -> **Application Log** 查看日志,你会看到:

```
Merging custom entitlements from my-entitlements.plist
Adding custom entitlement 'aps-environment'
Adding custom entitlement 'com.apple.developer.associated-domains'
Successfully merged 2 custom entitlement(s)
–––––––––––––––––––––––
<完整的 entitlements XML 内容>
–––––––––––––––––––––––
```

## 常见用途示例

### 添加推送通知权限

```xml
<key>aps-environment</key>
<string>production</string>
```

### 添加 App Groups

```xml
<key>com.apple.security.application-groups</key>
<array>
    <string>group.com.yourcompany.yourapp</string>
</array>
```

### 添加 Associated Domains (Universal Links)

```xml
<key>com.apple.developer.associated-domains</key>
<array>
    <string>applinks:yourdomain.com</string>
    <string>applinks:*.yourdomain.com</string>
</array>
```

### 添加 Keychain Sharing

```xml
<key>keychain-access-groups</key>
<array>
    <string>$(AppIdentifierPrefix)com.yourcompany.yourapp</string>
</array>
```

### 添加 iCloud 权限

```xml
<key>com.apple.developer.icloud-container-identifiers</key>
<array>
    <string>iCloud.com.yourcompany.yourapp</string>
</array>
<key>com.apple.developer.ubiquity-kvstore-identifier</key>
<string>$(TeamIdentifierPrefix)com.yourcompany.yourapp</string>
<key>com.apple.developer.icloud-services</key>
<array>
    <string>CloudKit</string>
</array>
```

## 注意事项

1. **文件格式**: 必须是标准的 plist XML 格式
2. **权限兼容性**: 确保你添加的权限与你的 Provisioning Profile 兼容
3. **覆盖规则**: 如果 key 已存在,你的自定义值会覆盖原值
4. **查看日志**: 建议在签名时打开日志查看最终的 entitlements
5. **清除选择**: 如果想取消自定义 entitlements,可以再次点击菜单选择然后点击"取消"

## 示例文件

项目中包含了 `custom-entitlements-example.plist` 文件,展示了常用的 entitlements 配置,你可以以此为模板创建自己的配置。

## 故障排查

### 签名失败

如果签名失败,可能是因为:
- 添加的 entitlement 与 Provisioning Profile 不兼容
- plist 格式错误
- 某些 entitlements 需要特定类型的证书

解决方法:
1. 打开 View -> Application Log 查看具体错误
2. 检查 plist 文件格式是否正确
3. 确认 Provisioning Profile 支持你添加的权限

### 如何查看最终的 entitlements

在签名过程中:
1. 打开 **View** -> **Application Log**
2. 搜索 "–––––––––––––––––––––––"
3. 在这两行之间就是最终的 entitlements 内容

## 更多 Entitlements 参考

完整的 entitlements 列表请参考:
- [Apple 官方文档: Entitlements](https://developer.apple.com/documentation/bundleresources/entitlements)
- 项目中的 `CUSTOM-ENTITLEMENTS-README.md` 文件
