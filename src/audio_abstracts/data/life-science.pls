<?xml version="1.0" encoding="UTF-8"?>
<!--
  Alias rules for life-science vocabulary.

  Alias rules are honoured by every ElevenLabs text-to-speech model, so
  this file is the safe default. Each <alias> is written the way a
  researcher says the term out loud, spelled phonetically in plain
  English, not the way it is written in a paper.

  Replacement is a literal string substitution performed before
  synthesis, so plural forms need their own lexeme only when the plural
  is not a simple suffix of the singular.
-->
<lexicon version="1.0"
         xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.w3.org/2005/01/pronunciation-lexicon
                             http://www.w3.org/TR/2007/CR-pronunciation-lexicon-20071212/pls.xsd"
         alphabet="ipa"
         xml:lang="en-GB">

  <!-- Methylation and epigenetics -->
  <lexeme><grapheme>CpG</grapheme><alias>see pee gee</alias></lexeme>
  <lexeme><grapheme>5mC</grapheme><alias>five methyl see</alias></lexeme>
  <lexeme><grapheme>5hmC</grapheme><alias>five hydroxymethyl see</alias></lexeme>
  <lexeme><grapheme>EWAS</grapheme><alias>ee-wass</alias></lexeme>
  <lexeme><grapheme>DMP</grapheme><alias>dee em pee</alias></lexeme>
  <lexeme><grapheme>DMR</grapheme><alias>dee em arr</alias></lexeme>
  <lexeme><grapheme>WGBS</grapheme><alias>whole genome bisulphite sequencing</alias></lexeme>
  <lexeme><grapheme>RRBS</grapheme><alias>arr arr bee ess</alias></lexeme>
  <lexeme><grapheme>bisulfite</grapheme><alias>bye-sulfite</alias></lexeme>
  <lexeme><grapheme>bisulphite</grapheme><alias>bye-sulfite</alias></lexeme>
  <lexeme><grapheme>methylome</grapheme><alias>methyl-ome</alias></lexeme>
  <lexeme><grapheme>Infinium</grapheme><alias>in-finny-um</alias></lexeme>
  <lexeme><grapheme>Illumina</grapheme><alias>ill-oo-mee-na</alias></lexeme>
  <!-- Matching is case sensitive, and papers write this both ways. -->
  <lexeme><grapheme>450K</grapheme><alias>four-fifty-kay</alias></lexeme>
  <lexeme><grapheme>450k</grapheme><alias>four-fifty-kay</alias></lexeme>
  <lexeme><grapheme>850K</grapheme><alias>eight-fifty-kay</alias></lexeme>
  <lexeme><grapheme>850k</grapheme><alias>eight-fifty-kay</alias></lexeme>
  <lexeme><grapheme>EPICv2</grapheme><alias>epic version two</alias></lexeme>

  <!-- Genetics and variation -->
  <lexeme><grapheme>GWAS</grapheme><alias>gee-wass</alias></lexeme>
  <lexeme><grapheme>SNP</grapheme><alias>snip</alias></lexeme>
  <lexeme><grapheme>SNPs</grapheme><alias>snips</alias></lexeme>
  <lexeme><grapheme>indel</grapheme><alias>in-del</alias></lexeme>
  <lexeme><grapheme>eQTL</grapheme><alias>ee kyoo tee ell</alias></lexeme>
  <lexeme><grapheme>mQTL</grapheme><alias>em kyoo tee ell</alias></lexeme>
  <lexeme><grapheme>MTHFR</grapheme><alias>em tee aitch eff arr</alias></lexeme>
  <lexeme><grapheme>BRCA1</grapheme><alias>brack-uh one</alias></lexeme>
  <lexeme><grapheme>BRCA2</grapheme><alias>brack-uh two</alias></lexeme>
  <lexeme><grapheme>APOE</grapheme><alias>ay-po-ee</alias></lexeme>
  <lexeme><grapheme>TP53</grapheme><alias>tee pee fifty-three</alias></lexeme>
  <lexeme><grapheme>CRISPR</grapheme><alias>crisper</alias></lexeme>
  <lexeme><grapheme>Cas9</grapheme><alias>cass nine</alias></lexeme>

  <!-- Transcriptomics and assays -->
  <lexeme><grapheme>qPCR</grapheme><alias>kyoo pee see arr</alias></lexeme>
  <lexeme><grapheme>RNA-seq</grapheme><alias>arr-en-ay seek</alias></lexeme>
  <lexeme><grapheme>scRNA-seq</grapheme><alias>single-cell arr-en-ay seek</alias></lexeme>
  <lexeme><grapheme>ATAC-seq</grapheme><alias>ay-tack seek</alias></lexeme>
  <lexeme><grapheme>ChIP-seq</grapheme><alias>chip seek</alias></lexeme>
  <lexeme><grapheme>miRNA</grapheme><alias>micro arr-en-ay</alias></lexeme>
  <lexeme><grapheme>siRNA</grapheme><alias>ess-eye arr-en-ay</alias></lexeme>
  <lexeme><grapheme>lncRNA</grapheme><alias>link arr-en-ay</alias></lexeme>
  <lexeme><grapheme>UTR</grapheme><alias>you tee arr</alias></lexeme>
  <lexeme><grapheme>TSS</grapheme><alias>tee ess ess</alias></lexeme>

  <!-- Reference genomes: the single most reliably mangled class -->
  <lexeme><grapheme>GRCh38</grapheme><alias>gee-arr-see-aitch thirty-eight</alias></lexeme>
  <lexeme><grapheme>GRCh37</grapheme><alias>gee-arr-see-aitch thirty-seven</alias></lexeme>
  <lexeme><grapheme>hg38</grapheme><alias>aitch-gee thirty-eight</alias></lexeme>
  <lexeme><grapheme>hg19</grapheme><alias>aitch-gee nineteen</alias></lexeme>

  <!-- Software and file formats -->
  <lexeme><grapheme>minfi</grapheme><alias>min-fee</alias></lexeme>
  <lexeme><grapheme>limma</grapheme><alias>lim-uh</alias></lexeme>
  <lexeme><grapheme>edgeR</grapheme><alias>edge arr</alias></lexeme>
  <lexeme><grapheme>DESeq2</grapheme><alias>dee-seek two</alias></lexeme>
  <lexeme><grapheme>ComBat</grapheme><alias>com-bat</alias></lexeme>
  <lexeme><grapheme>nf-core</grapheme><alias>en-eff core</alias></lexeme>
  <lexeme><grapheme>samtools</grapheme><alias>sam tools</alias></lexeme>
  <lexeme><grapheme>bedtools</grapheme><alias>bed tools</alias></lexeme>
  <lexeme><grapheme>BWA</grapheme><alias>bee double-you ay</alias></lexeme>
  <lexeme><grapheme>FASTQ</grapheme><alias>fast-cue</alias></lexeme>
  <lexeme><grapheme>VCF</grapheme><alias>vee see eff</alias></lexeme>

  <!-- Repositories and consortia -->
  <lexeme><grapheme>TCGA</grapheme><alias>tee see gee ay</alias></lexeme>
  <lexeme><grapheme>GEO</grapheme><alias>gee ee oh</alias></lexeme>
  <lexeme><grapheme>SRA</grapheme><alias>ess arr ay</alias></lexeme>
  <lexeme><grapheme>ENCODE</grapheme><alias>en-code</alias></lexeme>

  <!-- Statistics -->
  <lexeme><grapheme>FDR</grapheme><alias>eff dee arr</alias></lexeme>
  <lexeme><grapheme>Bonferroni</grapheme><alias>bon-fer-oh-nee</alias></lexeme>
  <lexeme><grapheme>CI</grapheme><alias>confidence interval</alias></lexeme>

  <!-- Latin, which English-trained models stress incorrectly -->
  <lexeme><grapheme>in vitro</grapheme><alias>in vee-troh</alias></lexeme>
  <lexeme><grapheme>in vivo</grapheme><alias>in vee-voh</alias></lexeme>
  <lexeme><grapheme>in silico</grapheme><alias>in sill-ee-koh</alias></lexeme>
  <lexeme><grapheme>de novo</grapheme><alias>day no-voh</alias></lexeme>

</lexicon>
