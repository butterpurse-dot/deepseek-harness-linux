import { describe, expect, it } from 'vitest'
import {
  desktopElectronBuilderArguments,
  parseDesktopPackageInvocation,
  resolveDesktopPackageTarget,
} from '../scripts/package-target.ts'
import { localLinuxPackageEnvironment } from '../scripts/desktop-package-environment.mjs'
import { selectOfficeEngine } from '../../../scripts/libreoffice-packages.mjs'

describe('Linux desktop packaging', () => {
  it('accepts linux targets on a matching host and rejects other hosts', () => {
    expect(resolveDesktopPackageTarget('linux-x64', 'linux', 'x64')).toMatchObject({
      name: 'linux-x64', platform: 'linux', arch: 'x64', builderPlatform: '--linux', builderArch: '--x64',
    })
    expect(resolveDesktopPackageTarget('linux-arm64', 'linux', 'arm64')).toMatchObject({
      name: 'linux-arm64', platform: 'linux', arch: 'arm64', builderPlatform: '--linux', builderArch: '--arm64',
    })
    expect(() => resolveDesktopPackageTarget('linux-x64', 'darwin', 'x64')).toThrow(/Linux build host/u)
    expect(() => resolveDesktopPackageTarget('linux-x64', 'linux', 'arm64')).toThrow(/requires an x64 Linux build host/u)
    expect(() => resolveDesktopPackageTarget('linux-arm64', 'linux', 'x64')).toThrow(/requires an arm64 Linux build host/u)
  })

  it('parses unsigned and publishing Linux invocations', () => {
    const invocation = parseDesktopPackageInvocation(['linux-x64', '--unsigned', '--publish'], 'linux', 'x64')
    expect(invocation.target.name).toBe('linux-x64')
    expect(invocation.unsigned).toBe(true)
    expect(invocation.publish).toBe(true)
    expect(invocation.directory).toBe(false)
  })

  it('passes the GitHub publish mode through to electron-builder', () => {
    const target = resolveDesktopPackageTarget('linux-x64', 'linux', 'x64')
    expect(desktopElectronBuilderArguments(target, false, undefined, true)).toEqual(expect.arrayContaining([
      '--linux', '--x64', '--publish', 'always',
    ]))
    expect(desktopElectronBuilderArguments(target, false)).toEqual(expect.arrayContaining(['--publish', 'never']))
  })

  it('builds an isolated unsigned Linux environment', () => {
    const environment = localLinuxPackageEnvironment({
      PATH: '/usr/bin', DSH_DESKTOP_APP_ID: 'com.example.other',
      DOWNLOAD_TEST_ORIGIN: 'https://updates.example.com', CSC_LINK: '/tmp/cert.p12',
    })
    expect(environment).toMatchObject({
      PATH: '/usr/bin', DSH_DESKTOP_APP_ID: 'com.deepseek.harness', DSH_DESKTOP_UNSIGNED: '1',
    })
    expect(environment.DOWNLOAD_TEST_ORIGIN).toBeUndefined()
    expect(environment.CSC_LINK).toBeUndefined()
  })

  it('uses the WASM Office engine on Linux', () => {
    expect(selectOfficeEngine({
      optionalDependencies: { '@deepseek-ai/libreoffice-kit-linux-x64': '1.0.0' },
    }, { platform: 'linux', arch: 'x64' })).toBe('wasm')
    expect(selectOfficeEngine({
      optionalDependencies: { '@deepseek-ai/libreoffice-kit-darwin-arm64': '1.0.0' },
    }, { platform: 'darwin', arch: 'arm64' })).toBe('darwin-arm64')
  })
})
