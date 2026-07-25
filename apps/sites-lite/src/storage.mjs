const DB_NAME = "infinity-arcana";
const DB_VERSION = 1;
const STORES = ["readings", "collection", "settings"];

function fallbackKey(store) {
  return `infinity-arcana:${store}`;
}

function localFallback() {
  const get = (store) => JSON.parse(globalThis.localStorage?.getItem(fallbackKey(store)) || "[]");
  return {
    async put(store, value) {
      const values = get(store).filter((item) => item.id !== value.id);
      values.push(value);
      globalThis.localStorage?.setItem(fallbackKey(store), JSON.stringify(values));
    },
    async all(store) { return get(store); },
    async replaceAll(data) {
      for (const store of STORES) globalThis.localStorage?.setItem(fallbackKey(store), JSON.stringify(data[store] || []));
    }
  };
}

export async function openStore() {
  if (!globalThis.indexedDB) return localFallback();
  try {
    const db = await new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => STORES.forEach((store) => request.result.objectStoreNames.contains(store) || request.result.createObjectStore(store, { keyPath: "id" }));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    const operation = (store, mode, action) => new Promise((resolve, reject) => {
      const request = db.transaction(store, mode).objectStore(store);
      const result = action(request);
      result.onsuccess = () => resolve(result.result);
      result.onerror = () => reject(result.error);
    });
    return {
      async put(store, value) { await operation(store, "readwrite", (objectStore) => objectStore.put(value)); },
      async all(store) { return (await operation(store, "readonly", (objectStore) => objectStore.getAll())) || []; },
      async replaceAll(data) {
        for (const store of STORES) {
          await operation(store, "readwrite", (objectStore) => objectStore.clear());
          for (const value of data[store] || []) await operation(store, "readwrite", (objectStore) => objectStore.put(value));
        }
      }
    };
  } catch {
    return localFallback();
  }
}

export async function exportStore(store) {
  const result = {};
  for (const name of STORES) result[name] = await store.all(name);
  return result;
}

export { STORES };
