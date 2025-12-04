const CACHE_NAME = 'aluno-portal-v10'; // Mudei a versão para forçar atualização
const IMAGES_CACHE_NAME = 'aluno-images-v1'; // Cache separado para imagens

const urlsToCache = [
    '/portal',
    '/portal/index.html',
    '/portal/css/style.css',
    '/portal/js/app.js',
    '/portal/js/api.js',
    '/portal/js/ui.js',
    '/portal/images/nova.png',
    '/portal/images/icone.png',
    '/portal/images/default-avatar.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// INSTALAÇÃO: Cacheia os arquivos estáticos do App Shell
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened static cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// ATIVAÇÃO: Limpa caches antigos se houver mudança de versão
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && cacheName !== IMAGES_CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// INTERCEPTAÇÃO DE REDE
self.addEventListener('fetch', event => {
    const requestUrl = new URL(event.request.url);

    // ESTRATÉGIA 1: IMAGENS (Cache First, depois Rede)
    // Verifica se é uma imagem (jpg, png, etc) OU se vem do seu bucket na nuvem (r2)
    if (requestUrl.pathname.match(/\.(jpg|jpeg|png|gif|webp)$/) || requestUrl.hostname.includes('r2.cloudflarestorage.com')) {
        event.respondWith(
            caches.open(IMAGES_CACHE_NAME).then(cache => {
                return cache.match(event.request).then(response => {
                    // Se achou no cache, retorna imediatamente (Rápido!)
                    if (response) return response;

                    // Se não, busca na rede, guarda no cache e retorna
                    return fetch(event.request).then(networkResponse => {
                        // Clona a resposta porque ela só pode ser consumida uma vez
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                });
            })
        );
        return; // Sai da função, pois já tratamos a imagem
    }

    // ESTRATÉGIA 2: ARQUIVOS ESTÁTICOS (Cache First)
    // Para CSS, JS e HTML do próprio app
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});