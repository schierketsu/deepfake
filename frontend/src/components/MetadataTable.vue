<template>
  <div class="space-y-4">
    <template v-if="fileType === 'document'">
      <div class="card-soft p-5">
        <h4 class="text-heading-lg font-bold text-ink">Изображения в документе</h4>
        <p class="mt-1 text-sm text-soft-700">
          Всего: {{ metadata.images_count || 0 }}, с признаками ИИ: {{ metadata.images_with_ai_count || 0 }}
        </p>
      </div>

      <div v-if="(metadata.images || []).length === 0" class="card-soft p-5 text-sm text-soft-700">
        В документе не найдено извлеченных изображений.
      </div>

      <div
        v-for="(img, index) in (metadata.images || [])"
        :key="`doc-image-${index}`"
        class="card-soft p-5"
      >
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
          <p class="font-semibold text-ink break-words">{{ index + 1 }}. {{ img.filename || 'Без имени' }}</p>
          <span class="status-chip bg-soft-900 text-accent-300">
            ИИ: {{ (img.ai_indicators && img.ai_indicators.ai_probability) ?? 0 }}%
          </span>
        </div>

        <p v-if="img.ai_indicators && img.ai_indicators.software_detected && img.ai_indicators.software_detected.length" class="text-sm text-soft-700">
          ПО: {{ img.ai_indicators.software_detected.join(', ') }}
        </p>
        <ul v-if="img.ai_indicators && img.ai_indicators.anomalies && img.ai_indicators.anomalies.length" class="mt-2 list-disc space-y-1 pl-5 text-sm text-soft-700">
          <li v-for="(anom, ai) in img.ai_indicators.anomalies" :key="ai">{{ anom }}</li>
        </ul>
      </div>
    </template>

    <template v-else>
      <div
        v-for="section in sections"
        :key="section.title"
        class="card-soft overflow-hidden"
      >
        <div class="border-b border-soft-300 bg-soft-100 px-4 py-3">
          <h4 class="font-semibold text-ink">{{ section.title }}</h4>
        </div>
        <div v-if="section.rows.length > 0" class="divide-y divide-soft-200 bg-soft-50">
          <div
            v-for="(row, idx) in section.rows"
            :key="`${section.title}-${idx}`"
            class="grid gap-2 px-4 py-3 md:grid-cols-[220px_1fr]"
          >
            <div class="text-sm font-semibold text-soft-700">{{ row.key }}</div>
            <div class="break-words font-mono text-sm text-ink">{{ row.value }}</div>
          </div>
        </div>
        <div v-else class="px-4 py-6 text-sm text-soft-700 bg-soft-50">
          Данные в этой секции отсутствуют.
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'MetadataTable',
  props: {
    metadata: {
      type: Object,
      required: true
    },
    fileType: {
      type: String,
      required: true
    }
  },
  computed: {
    groupedMetadata() {
      if (!this.metadata.exif || !this.metadata.exif._grouped_metadata) return null
      const grouped = this.metadata.exif._grouped_metadata
      if (typeof grouped !== 'object' || grouped === null) return null

      const filtered = {}
      for (const [sectionName, sectionData] of Object.entries(grouped)) {
        if (Array.isArray(sectionData) && sectionData.length > 0) {
          filtered[sectionName] = sectionData
        }
      }
      return Object.keys(filtered).length ? filtered : null
    },
    sections() {
      if (this.fileType === 'video') {
        return [
          this.buildSection('Метаданные контейнера', this.metadata.container),
          this.buildSection('Видео поток', this.metadata.video_stream),
          this.buildSection('Аудио поток', this.metadata.audio_stream),
          this.buildSection('Информация о кодировании', this.metadata.encoding_info),
        ].filter(Boolean)
      }

      if (this.fileType === 'image' && this.groupedMetadata) {
        return Object.entries(this.groupedMetadata).map(([sectionName, sectionData]) => {
          const rows = sectionData.map((item) => ({
            key: this.formatGroupedKey(item),
            value: this.formatGroupedValue(item),
          }))
          return { title: sectionName, rows }
        })
      }

      if (this.fileType === 'image') {
        return [
          this.buildSection('EXIF данные', this.filteredExifData),
          this.buildSection('XMP данные', this.filteredXmpData),
          this.buildSection('Характеристики изображения', this.filteredImageCharacteristics),
        ].filter(Boolean)
      }

      return []
    },
    filteredExifData() {
      return this.filterObject(this.metadata.exif, (key, value) => key !== 'error' && !key.startsWith('_') && this.hasValue(value))
    },
    filteredXmpData() {
      return this.filterObject(this.metadata.xmp, (key, value) => key !== 'error' && this.hasValue(value))
    },
    filteredImageCharacteristics() {
      const excludeKeys = ['suspicious_features', 'error']
      return this.filterObject(this.metadata.image_characteristics, (key, value) => !excludeKeys.includes(key) && this.hasValue(value))
    }
  },
  methods: {
    buildSection(title, source) {
      if (!source || typeof source !== 'object') return null
      const rows = Object.entries(source).map(([key, value]) => ({
        key: this.formatKey(key),
        value: this.formatValue(value, key)
      }))
      return { title, rows }
    },
    filterObject(obj, predicate) {
      if (!obj || typeof obj !== 'object') return {}
      const filtered = {}
      for (const [key, value] of Object.entries(obj)) {
        if (predicate(key, value)) {
          filtered[key] = value
        }
      }
      return filtered
    },
    hasValue(value) {
      return value !== null && value !== undefined && value !== ''
    },
    formatKey(key) {
      let formatted = String(key)
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/\s+/g, ' ')
        .trim()

      if (formatted.length > 0) {
        formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1)
      }
      return formatted
    },
    formatGroupedKey(item) {
      let rawKey = ''
      if (Array.isArray(item) && item.length >= 2) {
        rawKey = item[0]
      } else if (typeof item === 'object' && item !== null) {
        const keys = Object.keys(item)
        if (keys.length > 0) rawKey = keys[0]
      }
      if (typeof rawKey === 'string' && rawKey.includes(':')) {
        rawKey = rawKey.split(':').pop().trim() || rawKey
      }
      return this.formatKey(rawKey || 'Параметр')
    },
    formatGroupedValue(item) {
      if (Array.isArray(item) && item.length >= 2) {
        return this.formatValue(item[1], item[0])
      }
      if (typeof item === 'object' && item !== null) {
        const keys = Object.keys(item)
        if (keys.length > 0) {
          const key = keys[0]
          return this.formatValue(item[key], key)
        }
      }
      return 'N/A'
    },
    formatValue(value, key) {
      if (value === null || value === undefined) return 'N/A'

      if (Array.isArray(value)) {
        return value.map((v) => this.formatValue(v, key)).join(', ')
      }

      if (typeof value === 'object') {
        const json = JSON.stringify(value)
        return json.length > 300 ? json.substring(0, 300) + '...' : json
      }

      if (key === 'duration' && typeof value === 'string') {
        const seconds = parseFloat(value)
        if (!Number.isNaN(seconds)) {
          const minutes = Math.floor(seconds / 60)
          const secs = Math.floor(seconds % 60)
          return `${minutes}:${secs.toString().padStart(2, '0')}`
        }
      }

      if (key === 'bit_rate' && typeof value === 'string') {
        const bits = parseInt(value, 10)
        if (!Number.isNaN(bits)) {
          if (bits >= 1000000) return `${(bits / 1000000).toFixed(2)} Mbps`
          if (bits >= 1000) return `${(bits / 1000).toFixed(2)} Kbps`
          return `${bits} bps`
        }
      }

      const text = String(value)
      return text.length > 500 ? text.substring(0, 500) + '...' : text
    }
  }
}
</script>
