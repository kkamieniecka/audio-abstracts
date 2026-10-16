<?xml version="1.0" encoding="UTF-8"?>
<!--
  Phoneme rules for the subset of terms that alias spelling cannot fix.

  Phoneme rules are NOT supported by every model. See the compatibility
  table in README.md, and run the `doctor` subcommand against a model to
  confirm empirically for your key. When a rule cannot be applied the API
  rejects the request rather than silently ignoring it, so keep this file
  separate from the alias rules and opt in with the phonemes flag.

  Transcriptions are IPA, Received Pronunciation. Primary stress is the
  reason these exist: "epigenome" and "Illumina" are both stressed wrongly
  by English-trained models no matter how you respell them.
-->
<lexicon version="1.0"
         xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
         alphabet="ipa"
         xml:lang="en-GB">

  <lexeme><grapheme>CpG</grapheme><phoneme>ˌsiːpiːˈdʒiː</phoneme></lexeme>
  <lexeme><grapheme>GWAS</grapheme><phoneme>ˈdʒiːwɑːs</phoneme></lexeme>
  <lexeme><grapheme>EWAS</grapheme><phoneme>ˈiːwɑːs</phoneme></lexeme>
  <lexeme><grapheme>SNP</grapheme><phoneme>snɪp</phoneme></lexeme>
  <lexeme><grapheme>epigenome</grapheme><phoneme>ˌɛpɪˈdʒiːnəʊm</phoneme></lexeme>
  <lexeme><grapheme>epigenomic</grapheme><phoneme>ˌɛpɪdʒɪˈnɒmɪk</phoneme></lexeme>
  <lexeme><grapheme>methylome</grapheme><phoneme>ˈmɛθɪləʊm</phoneme></lexeme>
  <lexeme><grapheme>bisulfite</grapheme><phoneme>baɪˈsʌlfaɪt</phoneme></lexeme>
  <lexeme><grapheme>Illumina</grapheme><phoneme>ɪljuːˈmiːnə</phoneme></lexeme>
  <lexeme><grapheme>Infinium</grapheme><phoneme>ɪnˈfɪniəm</phoneme></lexeme>
  <lexeme><grapheme>minfi</grapheme><phoneme>ˈmɪnfiː</phoneme></lexeme>
  <lexeme><grapheme>limma</grapheme><phoneme>ˈlɪmə</phoneme></lexeme>
  <lexeme><grapheme>CRISPR</grapheme><phoneme>ˈkrɪspə</phoneme></lexeme>
  <lexeme><grapheme>Bonferroni</grapheme><phoneme>ˌbɒnfəˈrəʊni</phoneme></lexeme>
  <lexeme><grapheme>in vivo</grapheme><phoneme>ɪn ˈviːvəʊ</phoneme></lexeme>
  <lexeme><grapheme>in vitro</grapheme><phoneme>ɪn ˈviːtrəʊ</phoneme></lexeme>

</lexicon>
