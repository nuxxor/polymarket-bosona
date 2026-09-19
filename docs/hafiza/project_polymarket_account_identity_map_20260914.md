---
name: polymarket-account-identity-map-20260914
description: "Polymarket hesap adi -> proxy adres -> credential dosyasi eslesmesi (nuxxor / nuxxor2 / nuxxor4); 14 Eyl 2026 canli API ile dogrulandi"
metadata:
  type: project
---

# Polymarket hesap kimlik haritasi — 2026-09-14 dogrulandi

Kullanici adi `https://polymarket.com/api/profile/userData?address=<proxy>` ile cozulur
(`name` alani). Bu tek guvenilir yontem; repo notlarindaki takma adlar yanlis olabilir.

| Ad | Proxy (funder) | Credential dosyasi | sigType | Not |
|---|---|---|---|---|
| nuxxor | `0xfCdC8DbA317545dE64fFE202a13b2fb96608Fcc7` | `.env.live` (PM_API_* yok, `derive_api_key()` gerekir) | 2 Safe | ANA hesap, baska bot calisiyor |
| nuxxor2 | `0x7d9f2d22caaabe02cf451ff55a8e7a5447d12133` | `.env.live2` | 2 Safe | atil, 31 Tem'den beri islem yok |
| nuxxor4 | `0x899d92cABef0b6B7cBFc88f8dC69D8a839CC64E2` | `poly-lpbot/ops/accounts/taygun.env` (0600) | 3 DepositWallet | signer EOA `0x62937FFfCAaCc06f8651A0C11B06F40f2EA7802F` |

**Tuzak:** `WALLET_INVENTORY.md` nuxxor4'u "Dublin / Taygun" diye, `tasks/todo.md.bak_hlrs`
ise "nuxxor3" diye anar. Ucu de ayni cuzdan. Dosya adina guvenme, funder fingerprint
(sha256 of lowercase address) ile dogrula: nuxxor4 = `94adb4d69ab90cc0…`.

- Alias dosyalar (byte-identical DEGIL, kanonik olan `taygun.env`):
  `data/analysis/c3_live_20260718/c3_account.env`, `updown-pilot/pilot_account.env` (dizin artik yok).
- Teminat tokeni **pUSD** `0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB`, Polygon, 6 decimals.
  Duz USDC gondermek teminat olarak kredilenmez.
- `get_balance_allowance` proxy hesaplarda allowance'i **her zaman 0** dondurur (aktif islem
  yapan nuxxor'da da 0). Bu bir blokaj gostergesi DEGIL.
- SDK: `py_clob_client_v2` sart; eski SDK sigType 3'te "invalid order version" verir.
- Hesaplar arasi transfer receipt'leri: `~/.local/share/poly-lpbot/transfer_attempts/`.

Ilgili: [[shadow-pm-btc15m-momentum-20260913]]


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🔑 POLYMARKET HESAP KİMLİK HARİTASI (09-14): nuxxor=0xfCdC/.env.live, nuxxor2=0x7d9f/.env.live2, nuxxor4=0x899d92/poly-lpbot/ops/accounts/taygun.env; repo notları nuxxor4'ü "nuxxor3"/"Dublin" diye yanlış anıyor; teminat pUSD](project_polymarket_account_identity_map_20260914.md)
