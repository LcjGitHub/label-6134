<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import GiftList from './components/GiftList.vue'
import GiftFormModal from './components/GiftFormModal.vue'
import CategoryList from './components/CategoryList.vue'
import CategoryFormModal from './components/CategoryFormModal.vue'
import ReservationList from './components/ReservationList.vue'
import ReservationFormModal from './components/ReservationFormModal.vue'
import type { Gift } from './types/gift'
import type { Category } from './types/category'

const message = useMessage()

const activeTab = ref<'gifts' | 'categories' | 'reservations'>('gifts')

const giftListRef = ref<InstanceType<typeof GiftList> | null>(null)
const showGiftModal = ref(false)
const editingGift = ref<Gift | null>(null)

const categoryListRef = ref<InstanceType<typeof CategoryList> | null>(null)
const showCategoryModal = ref(false)
const editingCategory = ref<Category | null>(null)

const reservationListRef = ref<InstanceType<typeof ReservationList> | null>(null)
const showReservationModal = ref(false)

function handleCreateGift(): void {
  editingGift.value = null
  showGiftModal.value = true
}

function handleEditGift(gift: Gift): void {
  editingGift.value = gift
  showGiftModal.value = true
}

function handleGiftSaved(): void {
  const isEdit = editingGift.value !== null
  showGiftModal.value = false
  giftListRef.value?.reload()
  message.success(isEdit ? '记录已更新' : '记录已创建')
}

function handleGiftDeleted(): void {
  giftListRef.value?.reload()
  message.success('记录已删除')
}

function handleCreateCategory(): void {
  editingCategory.value = null
  showCategoryModal.value = true
}

function handleEditCategory(category: Category): void {
  editingCategory.value = category
  showCategoryModal.value = true
}

function handleCategorySaved(): void {
  const isEdit = editingCategory.value !== null
  showCategoryModal.value = false
  categoryListRef.value?.reload()
  message.success(isEdit ? '类别已更新' : '类别已创建')
}

function handleCategoryDeleted(): void {
  categoryListRef.value?.reload()
  message.success('类别已删除')
}

function handleCreateReservation(): void {
  showReservationModal.value = true
}

function handleReservationSaved(): void {
  showReservationModal.value = false
  reservationListRef.value?.reload()
}

function handleReservationDeleted(): void {
  reservationListRef.value?.reload()
  message.success('预约已取消')
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>社区旧物赠送流转记录</h1>
        <p class="subtitle">记录社区内旧物赠送与领取情况</p>
      </div>
      <n-button
        v-if="activeTab === 'gifts'"
        type="primary"
        @click="handleCreateGift"
      >
        新增记录
      </n-button>
      <n-button
        v-else-if="activeTab === 'categories'"
        type="primary"
        @click="handleCreateCategory"
      >
        新增类别
      </n-button>
      <n-button
        v-else
        type="primary"
        @click="handleCreateReservation"
      >
        新增预约
      </n-button>
    </header>

    <main class="page-main">
      <n-tabs v-model:value="activeTab" type="bar" :tab-padding="16" size="large">
        <n-tab-pane name="gifts" tab="赠送记录">
          <GiftList
            ref="giftListRef"
            @edit="handleEditGift"
            @deleted="handleGiftDeleted"
          />
        </n-tab-pane>
        <n-tab-pane name="categories" tab="类别管理">
          <CategoryList
            ref="categoryListRef"
            @edit="handleEditCategory"
            @deleted="handleCategoryDeleted"
          />
        </n-tab-pane>
        <n-tab-pane name="reservations" tab="领取预约">
          <ReservationList
            ref="reservationListRef"
            @deleted="handleReservationDeleted"
          />
        </n-tab-pane>
      </n-tabs>
    </main>

    <GiftFormModal
      v-model:show="showGiftModal"
      :gift="editingGift"
      @saved="handleGiftSaved"
    />

    <CategoryFormModal
      v-model:show="showCategoryModal"
      :category="editingCategory"
      @saved="handleCategorySaved"
    />

    <ReservationFormModal
      v-model:show="showReservationModal"
      @saved="handleReservationSaved"
    />
  </div>
</template>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 40px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.page-main {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
</style>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
    Arial, 'Noto Sans SC', sans-serif;
  background: #f5f7fa;
  color: #333;
}
</style>
