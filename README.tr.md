# VoiceHub Studio

VoiceHub Studio; metinden konuşmaya üretim, ses klonlama, doğal dille ses tasarımı, ses profilleri, dalga biçimi düzenleme ve model ince ayarı için yerel öncelikli bir Linux uygulamasıdır. Model katmanı olarak [kadirnar/voicehub](https://github.com/kadirnar/voicehub) kullanır.

[English documentation](README.md) | Türkçe belge

## Özellikler

- VoiceHub'daki 34 TTS bağdaştırıcısını çalışma zamanında bulur.
- Her modelin gerçek üretim ve yapılandırma parametrelerinden otomatik denetimler oluşturur.
- CPU, CUDA, CUDA aygıt numarası, MPS ve Intel XPU seçimi sunar.
- Konuşma üretimi, izinli ses klonlama, ses kaydı, ses tasarımı ve hazır konuşmacıları destekler.
- Kesme, sessizlik algılama, gürültü azaltma, perde, hız, kazanç, sıkıştırma, filtre, yumuşatma ve çapraz geçiş işlemleri içerir.
- Sesleri, varlıkları, projeleri, işleri, üretimleri ve eğitim çalışmalarını SQLite'ta kalıcı olarak saklar.
- İngilizce ve Türkçe arayüz, yerel API, koyu/açık tema ve Linux masaüstü penceresi içerir.

## Linux'a kurulum

NVIDIA GPU bulunan bir sistemde eksiksiz kullanıcı kurulumu:

```bash
git clone https://github.com/kadirnar/voicehub-studio.git
cd voicehub-studio
./scripts/install-linux.sh --cuda --system-deps
```

Yalnızca CPU kullanmak için:

```bash
./scripts/install-linux.sh --cpu --system-deps
```

Kurulum; Python 3.12 ortamını, uygun PyTorch paketini, VoiceHub'ı, yerel pencere bağımlılığını, uygulama menüsü girdisini, simgeyi ve `voicehub-studio` başlatıcısını hazırlar. Ardından uygulama menüsünden **VoiceHub Studio**'yu açabilirsiniz.

Kaynak dizininden doğrudan çalıştırmak için:

```bash
./scripts/run.sh
```

## Türkçe konuşma üretimi

Üst çubuktaki **TR** düğmesi tüm arayüzü Türkçeye geçirir. **Üret** sayfasındaki **Türkçe kurulumu** düğmesi:

1. Türkçeyi doğrudan destekleyen `Supertone/supertonic-3` modelini seçer.
2. Modelin beklediği dil kodunu `tr` yapar.
3. Türkçe örnek metni yerleştirir.
4. Bu seçimleri uygulama varsayılanı olarak kaydeder.

Model kitaplığında Türkçe destekli ek seçenekler de işaretlenir:

- `facebook/mms-tts-tur`: VITS üzerinden küçük ve doğrudan Türkçe sentez; CC-BY-NC-4.0 lisanslıdır.
- XTTS v2: `tr` dil koduyla, izinli referans sesten Türkçe klonlama.
- Zonos: `tr` dil koduyla ifadeli sentez veya klonlama.

Her kontrol noktasının lisansını ticari kullanımdan önce inceleyin. Klonlama özelliğini yalnızca kendi sesiniz veya açık kullanım izniniz bulunan seslerle kullanın.

## Eğitim bağımlılıkları

Model ince ayarı da kurulacaksa:

```bash
./scripts/install-linux.sh --cuda --training --system-deps
```

## Kaldırma

Uygulama başlatıcısını kaldırıp yerel verileri korumak için:

```bash
./scripts/uninstall-linux.sh
```

Yerel sesleri, üretimleri, ayarları ve önbellekleri de geri alınamaz biçimde silmek için yalnızca bilinçli olarak `--purge-data` seçeneğini ekleyin.

## Geliştirme testleri

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m build --wheel
```

Mimari ayrıntıları [docs/architecture.md](docs/architecture.md), araştırma kararları ise [docs/research.md](docs/research.md) dosyasındadır.
