---
lang: en
layout: fullscreen
permalink: /doc/admin-api/table/
ref: 249
title: Admin API table
---

This page displays the fullscreen table from [Admin API](/doc/admin-api/).

| call                                  | dest      | argument  | inside                                    | return                                                    | note |
| ------------------------------------- | --------- | --------- | ----------------------------------------- | --------------------------------------------------------- | ---- |
| `admin.vmclass.List`                   | `dom0`    | -         | -                                         | `<class>\n`                                               |
| `admin.vm.List`                        | `dom0|<vm>` | -         | -                                         | `<name> class=<class> state=<state>\n`                    |
| `admin.vm.Create.<class>`              | `dom0`    | template  | `name=<name> label=<label>`               | -                                                         |
| `admin.vm.CreateInPool.<class>`        | `dom0`    | template  | `name=<name> label=<label> `<br/>`pool=<pool> pool:<volume>=<pool>`   | -                                                         | either use `pool=` to put all volumes there, <br/>or `pool:<volume>=` for individual volumes - both forms are not allowed at the same time
| `admin.vm.CreateDisposable`            | template  | -         | -                                         | name                                                      | Create new DisposableVM, `template` is any AppVM with `dispvm_allowed` set to True, or `dom0` to use default defined in `default_dispvm` property of calling VM; VM created with this call will be automatically removed after its shutdown; the main difference from `admin.vm.Create.DispVM` is automatic (random) name generation.
| `admin.vm.Remove`                      | vm        | -         | -                                         | -                                                         |
| `admin.label.List`                     | `dom0`    | -         | -                                         | `<property>\n`                                            |
| `admin.label.Create`                   | `dom0`    | label     | `0xRRGGBB`                                | -                                                         |
| `admin.label.Get`                      | `dom0`    | label     | -                                         | `0xRRGGBB`                                                |
| `admin.label.Index`                    | `dom0`    | label     | -                                         | `<label-index>`                                           |
| `admin.label.Remove`                   | `dom0`    | label     | -                                         | -                                                         |
| `admin.property.List`                  | `dom0`    | -         | -                                         | `<property>\n`                                            |
| `admin.property.Get`                   | `dom0`    | property  | -                                         | `default={True|False} `<br/>`type={str|int|bool|vm|label|list} <value>`   | Type `list` is added in R4.1. Values are of type `str` and each entry is suffixed with newline character.
| `admin.property.GetAll`                | `dom0`    | -         | -                                         | `<property-name> <full-value-as-in-property.Get>\n`       | Get all the properties in one call. Each property is returned on a separate line and use the same value encoding as property.Get method, with an exception that newlines are encoded as literal `\n` and literal `\` are encoded as `\\`.
| `admin.property.GetDefault`            | `dom0`    | property  | -                                         | `type={str|int|bool|vm|label|list} <value>`               | Type `list` is added in R4.1. Values are of type `str` and each entry is suffixed with newline character.
| `admin.property.Help`                  | `dom0`    | property  | -                                         | `help`                                                    |
| `admin.property.HelpRst`               | `dom0`    | property  | -                                         | `help.rst`                                                |
| `admin.property.Reset`                 | `dom0`    | property  | -                                         | -                                                         |
| `admin.property.Set`                   | `dom0`    | property  | value                                     | -                                                         |
| `admin.vm.property.List`               | vm        | -         | -                                         | `<property>\n`                                            |
| `admin.vm.property.Get`                | vm        | property  | -                                         | `default={True|False} `<br/>`type={str|int|bool|vm|label|list} <value>`   | Type `list` is added in R4.1. Each list entry is suffixed with a newline character.
| `admin.vm.property.GetAll`             | vm        | -         | -                                         | `<property-name> <full-value-as-in-property.Get>\n`       | Get all the properties in one call. Each property is returned on a separate line and use the same value encoding as property.Get method, with an exception that newlines are encoded as literal `\n` and literal `\` are encoded as `\\`.
| `admin.vm.property.GetDefault`         | vm        | property  | -                                         | `type={str|int|bool|vm|label|type} <value>`               | Type `list` is added in R4.1. Each list entry is suffixed with a newline character.
| `admin.vm.property.Help`               | vm        | property  | -                                         | `help`                                                    |
| `admin.vm.property.HelpRst`            | vm        | property  | -                                         | `help.rst`                                                |
| `admin.vm.property.Reset`              | vm        | property  | -                                         | -                                                         |
| `admin.vm.property.Set`                | vm        | property  | value                                     | -                                                         |
| `admin.vm.feature.List`                | vm        | -         | -                                         | `<feature>\n`                                             |
| `admin.vm.feature.Get`                 | vm        | feature   | -                                         | value                                                     |
| `admin.vm.feature.CheckWithTemplate`   | vm        | feature   | -                                         | value                                                     |
| `admin.vm.feature.CheckWithNetvm`      | vm        | feature   | -                                         | value                                                     |
| `admin.vm.feature.CheckWithAdminVM`    | vm        | feature   | -                                         | value                                                     |
| `admin.vm.feature.CheckWithTemplateAndAdminVM`| vm | feature   | -                                         | value                                                     |
| `admin.vm.feature.Remove`              | vm        | feature   | -                                         | -                                                         |
| `admin.vm.feature.Set`                 | vm        | feature   | value                                     | -                                                         |
| `admin.vm.tag.List`                    | vm        | -         | -                                         | `<tag>\n`                                                 |
| `admin.vm.tag.Get`                     | vm        | tag       | -                                         | `0` or `1`                                                | retcode? |
| `admin.vm.tag.Remove`                  | vm        | tag       | -                                         | -                                                         |
| `admin.vm.tag.Set`                     | vm        | tag       | -                                         | -                                                         |
| `admin.vm.firewall.Get`                | vm        | -         | -                                         | `<rule>\n`                                                | rules syntax as in [firewall interface](/doc/vm-interface/#firewall-rules-in-4x) with addition of `expire=` and `comment=` options; `comment=` (if present) must be the last option
| `admin.vm.firewall.Set`                | vm        | -         | `<rule>\n`                                | -                                                         | set firewall rules, see `admin.vm.firewall.Get` for syntax
| `admin.vm.firewall.Reload`             | vm        | -         | -                                         | -                                                         | force reload firewall without changing any rule
| `admin.vm.device.<class>.Attach`       | vm        | device    | options                                   | -                                                         | `device` is in form `<backend-name>+<device-ident>` <br/>optional options given in `key=value` format, separated with spaces; <br/>options can include `persistent=True` to "persistently" attach the device (default is temporary)
| `admin.vm.device.<class>.Detach`       | vm        | device    | -                                         | -                                                         | `device` is in form `<backend-name>+<device-ident>`
| `admin.vm.device.<class>.Set.persistent`| vm       | device    | `True`\|`False`                            | -                                                         | `device` is in form `<backend-name>+<device-ident>`
| `admin.vm.device.<class>.List`         | vm        | -         | -                                         | `<device> <options>\n`                                    | options can include `persistent=True` for "persistently" attached devices (default is temporary)
| `admin.vm.device.<class>.Available`    | vm        | device-ident | -                                         | `<device-ident> <properties> description=<desc>\n`        | optional service argument may be used to get info about a single device, <br/>optional (device class specific) properties are in `key=value` form, <br/>`description` must be the last one and is the only one allowed to contain spaces
| `admin.pool.List`                      | `dom0`    | -         | -                                         | `<pool>\n`                                                |
| `admin.pool.ListDrivers`               | `dom0`    | -         | -                                         | `<pool-driver> <property> ...\n`                          | Properties allowed in `admin.pool.Add`
| `admin.pool.Info`                      | `dom0`    | pool      | -                                         | `<property>=<value>\n`                                    |
| `admin.pool.Add`                       | `dom0`    | driver    | `<property>=<value>\n`                    | -                                                         |
| `admin.pool.Set.revisions_to_keep`     | `dom0`    | pool      | `<value>`                                 | -                                                         |
| `admin.pool.Remove`                    | `dom0`    | pool      | -                                         | -                                                         |
| `admin.pool.volume.List`               | `dom0`    | pool      | -                                         | volume id                                                 |
| `admin.pool.volume.Info`               | `dom0`    | pool      | vid                                       | `<property>=<value>\n`                                    |
| `admin.pool.volume.Set.revisions_to_keep`| `dom0`  | pool      | `<vid> <value>`                           | -                                                         |
| `admin.pool.volume.ListSnapshots`      | `dom0`    | pool      | vid                                       | `<snapshot>\n`                                            |
| `admin.pool.volume.Snapshot`           | `dom0`    | pool      | vid                                       | snapshot                                                  |
| `admin.pool.volume.Revert`             | `dom0`    | pool      | `<vid> <snapshot>`                        | -                                                         |
| `admin.pool.volume.Resize`             | `dom0`    | pool      | `<vid> <size_in_bytes>`                   | -                                                         |
| `admin.pool.volume.Import`             | `dom0`    | pool      | `<vid>\n<raw volume data>`                | -                                                         |
| `admin.pool.volume.CloneFrom`          | `dom0`    | pool      | vid                                       | token, to be used in `admin.pool.volume.CloneTo`          | obtain a token to copy volume `vid` in `pool`;<br/>the token is one time use only, it's invalidated by `admin.pool.volume.CloneTo`, even if the operation fails |
| `admin.pool.volume.CloneTo`            | `dom0`    | pool      | `<vid> <token>`                           | -                                                         | copy volume pointed by a token to volume `vid` in `pool` |
| `admin.vm.volume.List`                 | vm        | -         | -                                         | `<volume>\n`                                              | `<volume>` is per-VM volume name (`root`, `private`, etc), `<vid>` is pool-unique volume id
| `admin.vm.volume.Info`                 | vm        | volume    | -                                         | `<property>=<value>\n`                                    |
| `admin.vm.volume.Set.revisions_to_keep`| vm        | volume    | value                                     | -                                                         |
| `admin.vm.volume.ListSnapshots`        | vm        | volume    | -                                         | snapshot                                                  | duplicate of `admin.pool.volume.`, but with other call params |
| `admin.vm.volume.Snapshot`             | vm        | volume    | -                                         | snapshot                                                  | id. |
| `admin.vm.volume.Revert`               | vm        | volume    | snapshot                                  | -                                                         | id. |
| `admin.vm.volume.Resize`               | vm        | volume    | size_in_bytes                             | -                                                         | id. |
| `admin.vm.volume.Import`               | vm        | volume    | raw volume data                           | -                                                         | id. |
| `admin.vm.volume.ImportWithSize`       | vm        | volume    | `<size_in_bytes>\n<raw volume data>`      | -                                                         | new version of `admin.vm.volume.Import`, allows new volume to be different size |
| `admin.vm.volume.Clear`                | vm        | volume    | -                                         | -                                                         | clear contents of volume |
| `admin.vm.volume.CloneFrom`            | vm        | volume    | -                                         | token, to be used in `admin.vm.volume.CloneTo`            | obtain a token to copy `volume` of `vm`;<br/>the token is one time use only, it's invalidated by `admin.vm.volume.CloneTo`, even if the operation fails |
| `admin.vm.volume.CloneTo`              | vm        | volume    | token, obtained with `admin.vm.volume.CloneFrom` | -                                                         | copy volume pointed by a token to `volume` of `vm` |
| `admin.vm.Start`                       | vm        | -         | -                                         | -                                                         |
| `admin.vm.Shutdown`                    | vm        | -         | -                                         | -                                                         |
| `admin.vm.Pause`                       | vm        | -         | -                                         | -                                                         |
| `admin.vm.Unpause`                     | vm        | -         | -                                         | -                                                         |
| `admin.vm.Kill`                        | vm        | -         | -                                         | -                                                         |
| `admin.backup.Execute`                 | `dom0`    | config id | -                                         | -                                                         | config in `/etc/qubes/backup/<id>.conf`, only one backup operation of given `config id` can be running at once |
| `admin.backup.Info`                    | `dom0`    | config id | -                                         | backup info                                               | info what would be included in the backup
| `admin.backup.Cancel`                  | `dom0`    | config id | -                                         | -                                                         | cancel running backup operation
| `admin.Events`                         | `dom0|vm` | -         | -                                         | events                                                    |
| `admin.vm.Stats`                       | `dom0|vm` | -         | -                                         | `vm-stats` events, see below                              | emit VM statistics (CPU, memory usage) in form of events
