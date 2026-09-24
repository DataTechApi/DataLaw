package com.datatech.datalaw.repository;

import com.datatech.datalaw.entity.Processo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface ProcessoRepository extends JpaRepository<Processo, UUID> {

    @Query(value = "select orgao_julgador_nome, count(id) as quantidade " +
            "from silver.processo where classe_nome ilike concat('%', :classeNome, '%') " +
            "group by orgao_julgador_nome order by orgao_julgador_nome", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorOrgaoJulgador(@org.springframework.data.repository.query.Param("classeNome") String classeNome);

    @Query(value = "select classe_nome, count(id) as quantidade " +
            "from silver.processo group by classe_nome order by quantidade desc", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorClasse();
}
