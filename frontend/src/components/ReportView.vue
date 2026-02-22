<template>
  <div class="content-block border-[3px] border-black">
    <!-- Заголовок отчета -->
    <div class="border-b-[3px] border-black p-6 bg-white">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="title-report">РЕЗУЛЬТАТЫ АНАЛИЗА</h2>
          <div v-if="fileInfo" class="mt-2">
            <p class="text-xs font-medium text-black">{{ fileInfo.name }}</p>
            <p class="text-xs text-gray-600">{{ formatFileSize(fileInfo.size) }}</p>
          </div>
        </div>
        <div class="text-right">
          <div class="text-xs text-gray-600 mb-1">Тип файла</div>
          <div class="title-report text-black">{{ result.file_type }}</div>
        </div>
      </div>
    </div>

    <div class="p-8 bg-white">
      <!-- Главный индикатор вероятности ИИ -->
      <div class="mb-10 border-[3px] border-black p-6 bg-white relative overflow-hidden min-h-[120px] flex items-center">
        <!-- Цветной фон: при 100% — без косой линии, при меньших — косая правая сторона -->
        <div
          class="absolute inset-y-0 left-0 transition-all duration-500"
          :style="{
            width: getVisualWidth(summary.ai_probability) + '%',
            backgroundColor: getProbabilityColor(summary.ai_probability),
            clipPath: summary.ai_probability >= 100 ? 'none' : 'polygon(0 0, 100% 0, calc(100% - 30px) 100%, 0 100%)'
          }"
        ></div>
        
        <!-- Контент поверх фона; при 100% весь текст белый -->
        <div class="relative z-10 w-full">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold mb-1" :class="summary.ai_probability >= 100 ? 'text-white' : (summary.ai_probability > 50 ? 'text-white' : 'text-black')">
                Вероятность ИИ-вмешательства
              </h3>
              <p class="text-sm mt-2" :class="summary.ai_probability >= 100 ? 'text-white' : (summary.ai_probability > 50 ? 'text-white' : 'text-gray-600')">{{ getProbabilityLabel(summary.ai_probability) }}</p>
            </div>
            <div class="text-right">
              <div
                class="title-report"
                :style="summary.ai_probability >= 100 ? { color: '#fff' } : {}"
              >
                {{ summary.ai_probability }}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Основная информация -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        <div class="border-[3px] border-black p-5 bg-white">
          <div class="mb-3">
            <span class="text-xs text-gray-600 uppercase tracking-wide">Местоположение</span>
          </div>
          <p class="text-base text-black font-medium">{{ summary.location || 'Не указано' }}</p>
        </div>
        
        <div class="border-[3px] border-black p-5 bg-white">
          <div class="mb-3">
            <span class="text-xs text-gray-600 uppercase tracking-wide">Дата и время</span>
          </div>
          <p class="text-base text-black font-medium">{{ summary.date_time || 'Не указано' }}</p>
        </div>
        
        <div class="border-[3px] border-black p-5 bg-white">
          <div class="mb-3">
            <span class="text-xs text-gray-600 uppercase tracking-wide">Источник</span>
          </div>
          <p class="text-base text-black font-medium break-words">{{ summary.source || 'Неизвестно' }}</p>
        </div>
      </div>
    
      <!-- По фактам из метаданных (C2PA / Content Credentials) -->
      <div v-if="evidenceList.length > 0" class="mb-10">
        <div class="border-[3px] border-black p-6 bg-white">
          <div class="mb-4">
            <h3 class="text-xl font-bold text-black mb-2">По фактам из метаданных</h3>
            <p class="text-xs text-gray-600">Вывод сделан на основе C2PA/Content Credentials и цепочки доверия, без интерпретаций.</p>
          </div>
          <ul class="space-y-3">
            <li
              v-for="(fact, index) in evidenceList"
              :key="index"
              class="flex items-start border-[3px] border-black p-4 bg-white"
            >
              <span class="inline-block w-6 h-6 border-[3px] border-black bg-black text-white text-xs font-bold flex items-center justify-center mr-3 flex-shrink-0 mt-0.5">{{ index + 1 }}</span>
              <div class="text-sm text-black leading-relaxed break-words">
                <p v-for="(paragraph, pIndex) in formatFactText(fact)" :key="pIndex" class="mb-2 last:mb-0">
                  {{ paragraph }}
                </p>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- Обнаруженные признаки ИИ -->
      <div v-if="aiIndicators.software_detected.length > 0 || aiIndicators.anomalies.length > 0" class="mb-10">
        <div class="border-[3px] border-black p-6 bg-white">
          <div class="mb-4">
            <h3 class="text-xl font-bold text-black">Обнаруженные признаки ИИ</h3>
          </div>
          
          <div v-if="aiIndicators.software_detected.length > 0" class="mb-6">
            <h4 class="text-sm font-semibold text-black mb-3 uppercase tracking-wide">
              Обнаруженное ПО:
            </h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="software in aiIndicators.software_detected"
                :key="software"
                class="px-4 py-2 border-[3px] border-black bg-black text-white text-xs font-medium"
              >
                {{ software }}
              </span>
            </div>
          </div>
          
          <div v-if="aiIndicators.anomalies.length > 0">
            <h4 class="text-sm font-semibold text-black mb-3 uppercase tracking-wide">
              Аномалии и подозрительные признаки:
            </h4>
            <div class="space-y-2">
              <div
                v-for="(anomaly, index) in aiIndicators.anomalies"
                :key="index"
                class="border-[3px] border-black p-3 bg-white flex items-start"
              >
                <span class="text-sm text-black">{{ anomaly }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Детальные метаданные (раскрывающийся блок) -->
      <div class="mb-10">
        <button
          @click="showMetadata = !showMetadata"
          class="w-full border-[3px] border-black p-4 bg-white hover:bg-gray-50 transition-colors flex items-center justify-between text-left"
        >
          <h3 class="text-xl font-bold text-black">Детальные метаданные</h3>
          <svg
            class="h-5 w-5 text-black transition-transform"
            :class="{ 'rotate-180': showMetadata }"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div
          v-show="showMetadata"
          class="border-x-[3px] border-b-[3px] border-black p-6 bg-white"
        >
          <MetadataTable :metadata="result.metadata" :file-type="result.file_type" />
        </div>
      </div>
      
      <!-- Кнопки экспорта -->
      <div class="flex flex-wrap gap-4 pt-6 border-t-[3px] border-black">
        <button
          @click="handleExportPDF"
          class="px-6 py-3 border-[3px] border-black bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors"
        >
          ЭКСПОРТ PDF
        </button>
        
        <button
          @click="handleExportJSON"
          class="px-6 py-3 border-[3px] border-black bg-white text-black text-sm font-medium hover:bg-gray-50 transition-colors"
        >
          ЭКСПОРТ JSON
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import MetadataTable from './MetadataTable.vue'
import { getReport } from '../services/api'

export default {
  name: 'ReportView',
  components: {
    MetadataTable
  },
  props: {
    result: {
      type: Object,
      required: true
    }
  },
  emits: ['export-pdf', 'export-json'],
  data() {
    return {
      showMetadata: false
    }
  },
  computed: {
    summary() {
      return this.result.summary || {}
    },
    aiIndicators() {
      return this.result.ai_indicators || {
        software_detected: [],
        anomalies: [],
        evidence_from_metadata: []
      }
    },
    evidenceList() {
      return this.aiIndicators.evidence_from_metadata || []
    },
    fileInfo() {
      return this.result.fileInfo || null
    }
  },
  methods: {
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    getProbabilityLabel(probability) {
      if (probability < 30) return 'Низкая'
      if (probability < 70) return 'Средняя'
      return 'Высокая'
    },
    
    getProbabilityColor(probability) {
      if (probability <= 20) return '#7AFC50' // зеленый
      if (probability <= 50) return '#FFEB3C' // желтый
      return '#DC2626' // красный
    },
    
    getVisualWidth(probability) {
      // При 100% — шкала заполнена полностью; при 90% — визуально 87%
      if (probability >= 100) return 100
      if (probability >= 90) return 87
      return probability
    },
    
    formatFactText(text) {
      // Разбиваем длинный текст на параграфы по точкам и двоеточиям
      if (!text) return []
      
      // Разбиваем по точкам, но сохраняем структуру
      const sentences = text.split(/\.\s+/).filter(s => s.trim())
      const paragraphs = []
      let currentParagraph = ''
      
      for (let i = 0; i < sentences.length; i++) {
        const sentence = sentences[i].trim()
        if (!sentence) continue
        
        // Если предложение очень длинное (более 150 символов), разбиваем его
        if (sentence.length > 150) {
          if (currentParagraph) {
            paragraphs.push(currentParagraph.trim() + '.')
            currentParagraph = ''
          }
          // Разбиваем длинное предложение по запятым или двоеточиям
          const parts = sentence.split(/[,:]\s+/)
          if (parts.length > 1) {
            paragraphs.push(parts[0] + ':')
            paragraphs.push(parts.slice(1).join(', '))
          } else {
            paragraphs.push(sentence)
          }
        } else {
          currentParagraph += (currentParagraph ? '. ' : '') + sentence
          // Если накопили достаточно текста или это последнее предложение
          if (currentParagraph.length > 200 || i === sentences.length - 1) {
            paragraphs.push(currentParagraph.trim() + (i === sentences.length - 1 ? '' : '.'))
            currentParagraph = ''
          }
        }
      }
      
      if (currentParagraph) {
        paragraphs.push(currentParagraph.trim() + '.')
      }
      
      return paragraphs.length > 0 ? paragraphs : [text]
    },
    
    handleExportPDF() {
      const reportUrl = getReport(this.result.report_url)
      window.open(reportUrl, '_blank')
      this.$emit('export-pdf', reportUrl)
    },
    
    handleExportJSON() {
      this.$emit('export-json', this.result)
    }
  }
}
</script>
