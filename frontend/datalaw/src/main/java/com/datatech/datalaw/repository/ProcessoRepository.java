package com.datatech.datalaw.repository;

import com.datatech.datalaw.entity.Processo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface ProcessoRepository extends JpaRepository<Processo, UUID> {

    @Query(value = "select orgao_julgador_nome, count(id) as quantidade " +
            "from silver.processo " +
            "where (:classeNome IS NULL OR :classeNome = '' " +
            "       OR similarity(imutable_unaccent(classe_nome), imutable_unaccent(:classeNome)) > 0.25) " +
            "group by orgao_julgador_nome order by quantidade desc", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorOrgaoJulgador(@Param("classeNome") String classeNome);

    @Query(value = "select classe_nome, count(id) as quantidade " +
            "from silver.processo group by classe_nome order by quantidade desc", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorClasse();

    @Query(value = "SELECT COALESCE(ROUND(100 * SUM(favoraveis + parciais * 0.5) / NULLIF(SUM(processos_com_resultado), 0), 2), 0) " +
            "FROM gold.process_results WHERE classe_nome = :classeNome", nativeQuery = true)
    Double findTaxaSucessoPorClasse(@org.springframework.data.repository.query.Param("classeNome") String classeNome);
}
