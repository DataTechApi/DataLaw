package com.datatech.datalaw.service;

import com.datatech.datalaw.repository.ProcessoRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProcessoServiceTest {

    @Mock
    private ProcessoRepository processoRepository;

    @InjectMocks
    private ProcessoService processoService;

    @Test
    void quantidadePorOrgaoJulgadorRepassaFiltroDeClasse() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"1ª Vara Cível", 10L});
        when(processoRepository.findQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal");
    }

    @Test
    void quantidadePorClasseRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Execução Fiscal", 7L});
        when(processoRepository.findQuantidadeProcessosPorClasse()).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorClasse()).isSameAs(esperado);
    }

    @Test
    void taxaSucessoPorClasseRetornaValorDoRepositorio() {
        when(processoRepository.findTaxaSucessoPorClasse("Procedimento Comum Cível")).thenReturn(62.5);

        assertThat(processoService.obterTaxaSucessoPorClasse("Procedimento Comum Cível")).isEqualTo(62.5);
    }
}
