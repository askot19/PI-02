/**
 * Viva Café & Restaurante — máscaras de campos e busca de endereço por CEP.
 *
 * - Aplica máscara de CPF (000.000.000-00), CEP (00000-000) e telefone,
 *   com o telefone alternando automaticamente entre o formato residencial
 *   (00) 0000-0000 (8 dígitos) e celular (00) 00000-0000 (9 dígitos)
 *   conforme a quantidade de números digitados.
 * - Ao completar um CEP válido, busca o endereço na API pública ViaCEP
 *   (https://viacep.com.br) e preenche automaticamente os campos de
 *   endereço, cidade e estado, caso existam na página.
 *
 * Basta marcar o campo com o atributo `data-mascara="cpf"`, `"cep"` ou
 * `"telefone"` — este arquivo cuida do resto.
 */

(function () {
    'use strict';

    function apenasDigitos(valor) {
        return (valor || '').replace(/\D/g, '');
    }

    function mascararCPF(valor) {
        let v = apenasDigitos(valor).slice(0, 11);
        v = v.replace(/(\d{3})(\d)/, '$1.$2');
        v = v.replace(/(\d{3})(\d)/, '$1.$2');
        v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        return v;
    }

    function mascararCEP(valor) {
        let v = apenasDigitos(valor).slice(0, 8);
        v = v.replace(/(\d{5})(\d)/, '$1-$2');
        return v;
    }

    function mascararTelefone(valor) {
        let v = apenasDigitos(valor).slice(0, 11);
        if (v.length <= 10) {
            // Residencial: (00) 0000-0000
            v = v.replace(/(\d{2})(\d)/, '($1) $2');
            v = v.replace(/(\d{4})(\d{1,4})$/, '$1-$2');
        } else {
            // Celular: (00) 00000-0000
            v = v.replace(/(\d{2})(\d)/, '($1) $2');
            v = v.replace(/(\d{5})(\d{1,4})$/, '$1-$2');
        }
        return v;
    }

    const MASCARAS = {
        cpf: mascararCPF,
        cep: mascararCEP,
        telefone: mascararTelefone,
    };

    function aplicarMascaras() {
        Object.keys(MASCARAS).forEach(function (tipo) {
            const aplicar = MASCARAS[tipo];
            document.querySelectorAll('[data-mascara="' + tipo + '"]').forEach(function (campo) {
                campo.addEventListener('input', function () {
                    campo.value = aplicar(campo.value);
                });
                // Formata um valor já preenchido (ex.: ao abrir a tela de edição).
                if (campo.value) {
                    campo.value = aplicar(campo.value);
                }
            });
        });
    }

    function definirFeedback(elemento, texto, tipo) {
        if (!elemento) return;
        elemento.textContent = texto;
        elemento.classList.remove('campo-ajuda--ok', 'campo-ajuda--erro');
        if (tipo) {
            elemento.classList.add('campo-ajuda--' + tipo);
        }
    }

    function initBuscaCep() {
        const campoCep = document.querySelector('[data-mascara="cep"]');
        if (!campoCep) return;

        const campoEndereco = document.getElementById('id_endereco');
        const campoCidade = document.getElementById('id_cidade');
        const campoEstado = document.getElementById('id_estado');
        const feedback = document.getElementById('cep-feedback');

        let ultimoCepBuscado = '';

        async function buscarEndereco() {
            const cep = apenasDigitos(campoCep.value);
            if (cep.length !== 8 || cep === ultimoCepBuscado) return;

            definirFeedback(feedback, 'Buscando endereço...', null);

            try {
                const resposta = await fetch('https://viacep.com.br/ws/' + cep + '/json/');
                if (!resposta.ok) {
                    throw new Error('Falha na consulta');
                }
                const dados = await resposta.json();

                if (dados.erro) {
                    definirFeedback(feedback, 'CEP não encontrado. Confira o número digitado.', 'erro');
                    return;
                }

                if (campoEndereco) campoEndereco.value = dados.logradouro || campoEndereco.value;
                if (campoCidade) campoCidade.value = dados.localidade || '';
                if (campoEstado) campoEstado.value = dados.uf || '';

                ultimoCepBuscado = cep;
                definirFeedback(feedback, 'Endereço preenchido automaticamente. Confira antes de salvar.', 'ok');
            } catch (erro) {
                definirFeedback(feedback, 'Não foi possível buscar o CEP agora. Preencha o endereço manualmente.', 'erro');
            }
        }

        campoCep.addEventListener('input', function () {
            if (apenasDigitos(campoCep.value).length === 8) {
                buscarEndereco();
            }
        });
        campoCep.addEventListener('blur', buscarEndereco);
    }

    document.addEventListener('DOMContentLoaded', function () {
        aplicarMascaras();
        initBuscaCep();
    });
})();
