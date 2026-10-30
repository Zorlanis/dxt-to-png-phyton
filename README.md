<div align="center">

# DXT → PNG

### Knight Online dokuları için klasör yapısını koruyan dönüştürücü

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Interface](https://img.shields.io/badge/Aray%C3%BCz-CLI-334155?style=flat-square)
![Version](https://img.shields.io/badge/S%C3%BCr%C3%BCm-0.1.0-2563EB?style=flat-square)
[![License](https://img.shields.io/badge/Lisans-MIT-168455?style=flat-square)](LICENSE)

**Yapımcı: Zorlanis**

[Kurulum](#kurulum) · [Kullanım](#kullanım) · [Formatlar](#desteklenen-formatlar) · [CLI seçenekleri](#cli-seçenekleri)

</div>

---

**DXT to PNG**, Knight Online `.dxt` doku dosyalarını PNG'ye dönüştüren bir Python
komut satırı aracıdır. Tek bir dosyayı işleyebilir veya seçtiğiniz klasördeki tüm
dokuları alt klasörleriyle birlikte tarayabilirsiniz. PNG'ler, kaynak klasörün
düzeni korunarak `outputs` altında toplanır.

## Öne çıkan özellikler

- **Klasör yapısını korur.** Aynı adlı dosyalar, bulundukları klasörlere göre ayrı tutulur.
- **Alt klasörleri tarar.** Bir kaynak klasör seçerek bütün doku ağacını dönüştürebilirsiniz.
- **Şifreli dokuları açar.** Varsayılan oyun anahtarını kullanan NTF sürüm 7 desteklenir.
- **Mevcut çıktıları korur.** Toplu işlemde daha önce oluşturulmuş PNG'ler atlanır.
- **İşlemi görünür kılar.** Taranan klasörler, dosya sonuçları ve sonuç özeti terminale yazılır.
- **Terminalden yönlendirir.** Klasör yolunu sorar, dosyaları sayar ve otomatik başlar.
- **İlerlemeyi gösterir.** İlerleme çubuğunda yapılan, kalan, atlanan ve hatalı dosya sayıları görünür.
- **Yapay zekâ ve otomasyona uygundur.** Soru sormayan mod, sürümlü JSON çıktısı ve çıkış kodları sunar.

## Kurulum

### Gereksinimler

| Bileşen | Gereksinim |
| --- | --- |
| Python | 3.11 veya üzeri |
| Pillow | 13.0.0 — kurulum sırasında otomatik yüklenir |
| Kullanım | Terminal / PowerShell / komut istemi |

Proje klasöründe aşağıdaki komutu çalıştırın:

```sh
python -m pip install .
```

Kurulumun ardından yardım ekranını açabilirsiniz:

```sh
dxt2png --help
```

> `dxt2png` komutu bulunamazsa proje klasöründen `python dxt2png.py` kullanın.
> Aşağıdaki örneklerdeki tüm seçenekler bu yöntemle de çalışır.

## Kullanım

### Terminal sihirbazı

Proje klasöründe uygulamayı seçenek vermeden başlatın:

```sh
python dxt2png.py
```

Kurulu komutla aynı ekranı açmak için `dxt2png` yazabilirsiniz. Uygulama DXT
klasörünün yolunu sorar. **Enter'a basarsanız varsayılan kaynak kabul edilir:**

```text
C:\NTTGame\KnightOnlineEn
```

Başka bir klasörün yolunu da yazabilir veya terminale yapıştırabilirsiniz.
Geçerli yol alındığında alt klasörler taranır, bulunan DXT sayısı gösterilir ve
**ek onay beklenmeden** dönüştürme başlar. Çıktılar seçilen kaynağın içindeki
`outputs` klasörüne, özgün klasör yapısıyla yazılır. Geçersiz bir yol girilirse
yeniden klasör yolu istenir.

Sihirbazı açıkça başlatmak için:

```sh
dxt2png --interactive
```

### 1. Tek dosya dönüştürme

```sh
dxt2png item.dxt
```

Girdi dosyasının yanında `item.png` oluşturulur. Çıktı adını değiştirmek için:

```sh
dxt2png item.dxt -o item_preview.png
```

Tek dosya modunda çıktı dosyasının üst klasörü önceden bulunmalıdır.

### 2. Bir klasördeki bütün dokuları dönüştürme

```sh
dxt2png -d textures
```

`textures` klasörü ve alt klasörlerindeki `.dxt` dosyaları taranır. Sonuçlar
`textures/outputs` içine yazılır; gerekli alt klasörler otomatik oluşturulur.

**Kaynak klasör**

```text
textures/
├── item.dxt
├── ui/
│   └── menu.dxt
└── characters/
    └── armor.dxt
```

**Oluşturulan çıktılar**

```text
textures/outputs/
├── item.png
├── ui/
│   └── menu.png
└── characters/
    └── armor.png
```

### 3. Farklı bir çıktı klasörü seçme

```sh
dxt2png -d textures -o converted
```

Bu örnekte klasör yapısı `converted` altında oluşturulur. Göreli çıktı yolları,
terminalin çalışma dizinine göre değerlendirilir.

### 4. Varsayılan oyun klasörünü dönüştürme

```sh
dxt2png -d
```

`C:\NTTGame\KnightOnlineEn` klasörü ve alt klasörleri taranır.
Terminalin çalışma klasörünü kullanmak için yolu açıkça belirtin:

```sh
dxt2png -d .
```

### Windows örneği

```powershell
python dxt2png.py -d "C:\Games\KnightOnline\Textures" -o "C:\Converted Textures"
```

Boşluk içeren dosya ve klasör yollarını tırnak içine alın.

## Desteklenen formatlar

| Girdi formatı | Açıklama | Çıktı |
| --- | --- | --- |
| DXT1 / BC1 | Renk ve ikili saydamlık | PNG |
| DXT2 / BC2 | Önceden alfa ile çarpılmış renk ve açık alfa | PNG |
| DXT3 / BC2 | Renk ve açık alfa değerleri | PNG |
| DXT4 / BC3 | Önceden alfa ile çarpılmış renk ve enterpolasyonlu alfa | PNG |
| DXT5 / BC3 | Renk ve enterpolasyonlu alfa | PNG |
| A8R8G8B8 | 32 bit renk ve alfa | PNG |
| X8R8G8B8 | 32 bit renk, tam opak çıktı | PNG |
| A1R5G5B5 | 16 bit renk ve 1 bit alfa | PNG |
| A4R4G4B4 | 16 bit renk ve 4 bit alfa | PNG |
| TGA 2.0 | `.dxt` olarak saklanan, `TRUEVISION-XFILE.` imzalı dosyalar | PNG |

**DXT1, DXT2, DXT3, DXT4 ve DXT5** ailesinin tamamı desteklenir.
DXT2 ve DXT4 renkleri, PNG'nin kullandığı alfa gösterimine dönüştürülür.
Alfa kanalı destekleyen dokuların saydamlığı korunur. Şifreli NTF sürüm 7 dosyaları
varsayılan oyun anahtarıyla açılır; CLI üzerinden özel anahtar girilemez.

Yalnızca en üst mip seviyesi dönüştürülür. Boyut sınırı her eksende **1–8192 piksel**dir.

## CLI seçenekleri

```text
dxt2png [INPUT] [-d [DIR]] [-o PATH] [--json]
```

| Seçenek | Açıklama |
| --- | --- |
| `INPUT` | Dönüştürülecek dosya veya kaynak klasör. |
| `-d, --directory [DIR]` | Kaynak klasörü alt klasörleriyle tarar. DIR verilmezse `C:\NTTGame\KnightOnlineEn` kullanılır. |
| `-o, --output PATH` | Tek dosya için çıktı adı; toplu işlem için çıktı kök klasörü. |
| `--json` | İşlem olaylarını ayrı JSON satırları olarak yazar. |
| `-i, --interactive` | Klasör yolunu soran terminal sihirbazını açar. |
| `--non-interactive` | Kullanıcıya soru sormaz; kaynak verilmezse varsayılan oyun klasörünü kullanır. |
| `--no-color` | Terminal renklerini kapatır. `NO_COLOR` ortam değişkeni de desteklenir. |
| `-h, --help` | Yardım ekranını gösterir. |
| `-V, --version` | Sürümü ve yapımcı bilgisini gösterir. |

`INPUT` ile `-d` birlikte kullanılmaz. Kaynak klasör, doğrudan `INPUT` olarak da verilebilir:

```sh
dxt2png textures
```

## İşlem takibi

Terminalde mavi bir ilerleme çubuğu, dosya sayaçları ve sonuç özeti gösterilir:

```text
  3 DXT dosyası bulundu.
  Çıktı: .../textures/outputs
  Dönüştürme otomatik başlıyor…

  [██████████████████████████] 100%  Yapılan:2  Kalan:0  Atlanan:1  Hata:0

  TAMAMLANDI
  2 PNG oluşturuldu · 1 atlandı · 0 hata · 0.4 sn
```

| Durum | Anlamı |
| --- | --- |
| `Taranıyor` / `TARA` | Klasör içeriği taranıyor. |
| `Yapılan` | Başarıyla oluşturulan yeni PNG sayısı. |
| `Kalan` | Henüz işlenmemiş DXT sayısı. |
| `Atlanan` | Çıktısı zaten mevcut olduğu için geçilen dosya sayısı. |
| `HATA` | Dosya okunamadı, format desteklenmiyor veya çıktı yazılamadı. |

Bir dosyanın dönüşümünde hata oluşursa diğer dosyalar işlenmeye devam eder.
Klasör taramasını engelleyen bir erişim hatası ise işlemi durdurur.
Terminalde ilerleme satırı yerinde yenilenir; yönlendirilmiş çıktıda satır satır
yazılır. Atlanan ve hatalı dosyalar da işlenmiş sayıldığı için ilerleme yüzdesi
yalnızca yeni PNG sayısından hesaplanmaz.

## Yapay zekâ ve otomasyon

AI ajanları, görev zamanlayıcıları ve scriptler kullanıcı girişi beklememek için
`--non-interactive` kullanabilir:

```sh
python dxt2png.py --non-interactive -d "C:\NTTGame\KnightOnlineEn" --json
```

Varsayılan kaynak klasör için:

```sh
python dxt2png.py --non-interactive --json
```

`--json` tek başına da soru sormayan modu etkinleştirir. Standart girdi terminal
değilse seçenek verilmeden çalıştırmak da varsayılan kaynakla otomatik başlar.
Varsayılan klasör bulunamazsa işlem `1` koduyla sonlanır; girdi beklemez.
`--interactive` ile `--json` birlikte kullanılamaz.

### JSON çıktı sözleşmesi

```sh
dxt2png -d textures --json
```

JSON modunda standart çıktı yalnızca JSON satırları içerir; renk kodları,
ilerleme çubukları veya klasör soruları eklenmez. Her olayda `schema_version: 1`
bulunur. Olay türleri `scanning`, `found`,
`file` ve `summary` değerleridir. Dosya durumları `converted`, `skipped` veya
`failed` olabilir. İşlem tamamlandığında örneğin şu özet üretilir:

```json
{"schema_version": 1, "event": "summary", "total": 12, "converted": 9, "skipped": 2, "failed": 1, "processed": 12, "remaining": 0, "percent": 100.0}
```

Genel hatalar `error`, kullanıcı tarafından durdurulan işlemler `cancelled`
olayıyla bildirilir.

| Alan | Anlamı |
| --- | --- |
| `total` | Tarama tamamlandıktan sonra bulunan toplam DXT sayısı. |
| `converted` | Oluşturulan PNG sayısı. |
| `skipped` | Mevcut çıktı nedeniyle atlanan dosya sayısı. |
| `failed` | Dönüştürme hatası veren dosya sayısı. |
| `processed` | `converted + skipped + failed`. |
| `remaining` | Henüz işlenmemiş dosya sayısı. |
| `percent` | İşlenen dosyalara göre yüzde ilerleme. |

Tarama sürerken toplam henüz bilinmediği için sayaçlar `0` olur. Ajanlar toplam
dosya sayısı için `found`, nihai sonuç için `summary` olayını kullanmalıdır.

### Çıkış kodları

| Kod | Anlamı |
| --- | --- |
| `0` | İşlem başarıyla tamamlandı. Mevcut çıktılar atlanmış olabilir. |
| `1` | Dosya okuma, dönüştürme veya yazma hatası oluştu. |
| `2` | Komut satırı seçenekleri eksik veya geçersiz. |
| `130` | İşlem `Ctrl+C` ile durduruldu. |

## Çıktı koruması ve devam etme

- Mevcut dosyaların üzerine yazılmaz. Tek dosya modunda aynı çıktı adı hata üretir;
  toplu işlemde mevcut çıktı atlanır.
- `Ctrl+C` ile durdurulduğunda tamamlanan PNG'ler korunur, yazımı kesilen PNG temizlenir.
- Aynı komutu yeniden çalıştırmak, tamamlanan dosyaları atlayarak devam etmeyi sağlar.
- Çıktı klasörü taramaya alınmaz. Girdi ve çıktı kök klasörleri aynı olamaz.
- Sembolik bağlantılar ve Windows yeniden ayrıştırma noktaları takip edilmez.
- `.dxt` uzantısı büyük/küçük harfe duyarsız eşleştirilir.

## Lisans

**Copyright © 2026 Zorlanis.** Proje [MIT lisansı](LICENSE) ile sunulur.
Uyarlanan bileşenlerin telif bildirimleri
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) dosyasında yer alır.
