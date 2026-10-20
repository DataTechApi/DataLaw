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
    void quantidadePorOrgaoJulgadorRepassaFiltroDeClasseEAssunto() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"1ª Vara Cível", 10L});
        when(processoRepository.findQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "IPTU")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "IPTU")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "IPTU");
    }

    @Test
    void quantidadePorClasseRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Execução Fiscal", 7L});
        when(processoRepository.findQuantidadeProcessosPorClasse("IPTU")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorClasse("IPTU")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorClasse("IPTU");
    }

    @Test
    void quantidadePorAssuntoRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Dano Moral", 15L});
        when(processoRepository.findQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano");
    }

    @Test
    void taxaSucessoPorClasseRetornaValorDoRepositorio() {
        when(processoRepository.findTaxaSucessoPorClasse("Procedimento Comum Cível")).thenReturn(62.5);

        assertThat(processoService.obterTaxaSucessoPorClasse("Procedimento Comum Cível")).isEqualTo(62.5);
    }

    @Test
    void taxaSucessoPorAssuntoRetornaValorDoRepositorio() {
        when(processoRepository.findTaxaSucessoPorAssunto("Dano Moral")).thenReturn(48.25);

        assertThat(processoService.obterTaxaSucessoPorAssunto("Dano Moral")).isEqualTo(48.25);
    }

    @Test
    void precedentesPorAssuntoRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Tema 1234", "STJ"});
        when(processoRepository.findPrecedentesPorAssunto("Dano Moral")).thenReturn(esperado);

        assertThat(processoService.obterPrecedentesPorAssunto("Dano Moral")).isSameAs(esperado);
        verify(processoRepository).findPrecedentesPorAssunto("Dano Moral");
    }
}
