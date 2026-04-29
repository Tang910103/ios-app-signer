# TestFlight 外部分组独立测试

这个脚本只测试下面这条链路，不做 IPA 上传：

- 查找 App Store Connect 里的 App
- 查找或创建 `External Testing Group`
- 查找或启用 `Public Link`
- 把现有的已处理 build 挂到这个测试组

脚本文件：

- `scripts/testflight_external_group_flow.py`

## 只测试创建/查询外部分组和公开链接

```bash
python3 scripts/testflight_external_group_flow.py \
  --api-key-id "YOUR_KEY_ID" \
  --issuer-id "YOUR_ISSUER_ID" \
  --private-key "/Users/liuxiang/.private_keys/AuthKey_YOUR_KEY_ID.p8" \
  --bundle-id "com.example.app" \
  --external-group "UAT" \
  --public-link-limit 200 \
  --skip-attach-build
```

## 测试创建分组并把现有 build 挂到组

```bash
python3 scripts/testflight_external_group_flow.py \
  --api-key-id "YOUR_KEY_ID" \
  --issuer-id "YOUR_ISSUER_ID" \
  --private-key "/Users/liuxiang/.private_keys/AuthKey_YOUR_KEY_ID.p8" \
  --bundle-id "com.example.app" \
  --external-group "UAT" \
  --build-version "2.3.1" \
  --build-number "231"
```

## 可选参数

- `--app-id`
  直接指定 App Store Connect 的 app id，可替代 `--bundle-id`
- `--build-id`
  直接指定某个 ASC build id 挂组
- `--public-link-limit`
  启用公开链接时设置测试人数上限

## 常见前置条件

- App Store Connect 中必须先存在一个 `Internal Testing` 组，Apple 才允许创建 `External Testing` 组
- 你的 API Key 所属账号至少要对该 App 有足够权限，否则查询 App、创建组、启用链接都会失败
- 要挂到测试组的 build 必须已经在 App Store Connect 处理完成，通常是 `VALID`
